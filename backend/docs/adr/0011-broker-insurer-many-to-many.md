# ADR 0011: Broker↔Insurer many-to-many, and its RLS consequence

## Status
Accepted.

## Context
`broker_insurer_assignments` was built "many-to-many-ready" from Phase 1 (see its own docstring, and ADR-adjacent notes in `CLAUDE.md`) but enforced strictly 1:1: a partial unique index on `broker_id` alone meant a broker could have at most one active insurer assignment, system-wide. Product requirement: a broker genuinely works with several insurers at once, and vice versa, with a dashboard selector on each side to narrow to one counterparty (default: aggregate across all).

Lifting the 1:1 constraint touches more than the join table, because `get_tenant_id` (`app/core/deps.py`) — the single function that resolves "which insurer" for every broker-scoped request and sets the Postgres RLS session GUC (`app.current_tenant_id`, ADR 0006) — depended on there being exactly one active assignment to resolve.

## Decisions

1. **The join table's uniqueness moves from `(broker_id)` to `(broker_id, insurance_company_id)`**, both partial on `is_active`. A given pair can't be double-active; a broker can have many different active pairs. `assign_broker_to_insurer` changes from "deactivate the current one, insert a new one" to "activate this specific pair, idempotently" — it never touches the broker's other assignments. A new `unassign_broker_from_insurer` deactivates one pair without affecting any other.

2. **`get_tenant_id` stops resolving a single insurer for broker roles.** It now always returns `None` for a broker actor (never queries the assignment table, never 409s on "no active assignment" — a broker with zero assignments is a valid state, not an error). The three things this function used to conflate for a broker caller are pulled apart:
   - **RLS context** — still set on every request, but keyed off the broker's own stable `broker_id`, not a resolved insurer.
   - **Read-narrowing to one counterparty** — a new, explicit, validated dependency (`get_broker_insurer_filter` / `get_insurer_broker_filter`) driven by an optional query param, checked against the caller's actual active assignments. Omitted means aggregate across every counterparty.
   - **Which insurer a new financial row belongs to** — no longer resolved from actor context at all. `payment_service.initiate_payment` and `bulk_payment_service.initiate_bulk_payment` derive it directly from the target installment's policy (the one unambiguous source of truth), and bulk payments reject a batch that spans more than one insurer — the existing "one debit, one settlement" invariant doesn't have a single insurer to settle to otherwise. Policy/policyholder creation (now insurer-only, see below) takes the insurer from the actor's own resolved tenant and the broker from an explicit, validated request field.

3. **RLS needs a second GUC, `app.current_broker_id`.** This is the part worth flagging loudly: ADR 0006's policy treats an *unset* `app.current_tenant_id` as "cross-tenant, see everything" — correct for `insureflow_admin`, whose `get_tenant_id` also returns `None`. Once a broker's `get_tenant_id` returns `None` too, without a second signal the two cases become indistinguishable at the RLS layer, and a broker would silently gain admin-level cross-tenant visibility into every insurer's `payments`/`payment_batches`/`policies`/`policyholders` rows.

   The fix: `app.current_broker_id` is set to the broker's own id on every broker-actor request (via `_set_rls_context`, the renamed/extended `_set_rls_tenant_context`), and the policy on those four tables (not `settlement_payouts` — no `broker_id` column there, and brokers never hold `VIEW_SETTLEMENTS`) becomes:
   ```sql
   (NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL
    AND NULLIF(current_setting('app.current_broker_id', true), '') IS NULL)
   OR insurance_company_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
   OR broker_id = NULLIF(current_setting('app.current_broker_id', true), '')::uuid
   ```
   True cross-tenant (admin) now requires *both* GUCs unset, not just one.

4. **`app.current_tenant_id` is reserved exclusively for insurer-actor scoping — never for a broker's dashboard narrowing selection.** This is the specific mistake the design deliberately avoids: if a broker's insurer-picker were implemented by setting `app.current_tenant_id` to the selected insurer (instead of a plain app-layer `WHERE` clause), the RLS policy's `insurance_company_id = current_tenant_id` branch would grant that broker visibility into *every other broker's* rows under that same insurer — the GUC has no notion of "and also mine only." Counterparty narrowing for both broker and insurer dashboards is implemented purely as an additional app-layer predicate, layered on top of the RLS boundary (`broker_id`/`insurance_company_id` respectively), never expressed through a GUC.

## Consequences
- `tests/security/test_row_level_security.py` needs new cases proving: `app.current_broker_id` alone grants a broker their own rows; it does not grant visibility into a different broker's rows under a shared insurer; `WITH CHECK` rejects an insert claiming a mismatched `broker_id`; both GUCs unset still means fully cross-tenant (regression guard on existing `insureflow_admin` behavior).
- Every one of the ~20 existing `get_tenant_id` call sites had to be re-examined for whether it silently assumed a broker always resolves to a concrete tenant id. All but four (the two payment-initiation paths, and the two now-insurer-only creation endpoints) already carried an independent `broker_id`-based ownership filter alongside `tenant_id`, so they tolerate the new `None` safely; the four exceptions are handled explicitly (§2 above).
- `settlement_payouts`' RLS policy is unchanged — this ADR only extends the four broker-touched tables' policy, deliberately narrow in scope like ADR 0006 itself.
