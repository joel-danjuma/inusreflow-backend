# ADR 0010: Audit log retention policy (provisional)

## Status
Provisional — pending regulatory/compliance sign-off, same posture already taken for the kobo-rounding remainder rule (`docs/adr/0001-kobo-rounding.md`) and the reconciliation-mismatch handling (`docs/adr/0005-reconciliation-scope.md`). PRD §14 open question #8 explicitly left the retention period unconfirmed.

## Context
`audit_logs` (`app/models/audit.py`) is insert-only and immutable by construction — there is no update/delete code path against it anywhere in `app/services/audit_service.py`, and every state-changing service function in the codebase calls `record_audit_log` inside the same transaction as the change it describes (onboarding approvals, commission config changes, payment/batch/settlement state transitions, rate-limit rejections are logged via structlog/metrics instead since they aren't entity state changes). The table has grown every phase since Phase 0 and currently has no retention, archival, or deletion mechanism — every row ever written is retained forever by default.

For a fintech-adjacent product handling premium collection and settlement, regulatory retention requirements (e.g. how long financial/audit records must be kept, in which jurisdiction, in what form) are a compliance question, not an engineering one — Insureflow doesn't yet have confirmed guidance on which regulator's rules apply or what they require.

## Decision
1. **Retain indefinitely until regulatory guidance is confirmed.** No deletion, archival, or TTL job is built in this phase. This is the safer default for an audit trail — under-retaining audit records in a regulated domain is a worse failure mode than the storage cost of over-retaining them.
2. **No code currently deletes or mutates an `audit_logs` row, and none should be added** until a confirmed retention period exists. If/when one is confirmed, the implementation should be an explicit, separately-reviewed archival job (e.g. move rows older than the retention window to cold storage, or delete per a documented legal basis) — not a casual addition to this table's existing insert path.
3. **This ADR is the flag for that future work.** When retention guidance is confirmed, update this document (status → Accepted, with the actual retention period and jurisdiction it applies to) rather than silently introducing a cleanup job without revisiting the decision record.

## Consequences
- `audit_logs` will grow unbounded for the lifetime of this deployment until this ADR is revisited — acceptable for the current build/testing scale, but worth monitoring table size/storage cost as real transaction volume accumulates in a live deployment.
- Any future archival/deletion job must preserve the table's insert-only invariant for *retained* rows (no in-place mutation of historical records) and should itself be audit-logged or otherwise traceable, so deleting old audit records doesn't itself become an unaudited action.
