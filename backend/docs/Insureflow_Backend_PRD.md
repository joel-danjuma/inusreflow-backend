# Product Requirements Document: Insureflow (Backend Service)

| | |
|---|---|
| **Product** | Insureflow — Insurance Premium Collection & Settlement Platform |
| **Component** | Backend Service (API only — no frontend/UI in scope) |
| **Version** | 0.1 (Draft for Review) |
| **Status** | Draft |
| **Stack** | Python, FastAPI, Pydantic, PostgreSQL, Redis/Celery, Squad (GTBank) Payment API |
| **Last Updated** | 2026-06-22 |

---

## 1. Purpose & Scope

Insureflow is a multi-tenant backend platform that lets **insurance companies** onboard and manage **brokers**, who in turn create **policyholders (users)** and **policies**, and collect **premiums** on behalf of the insurance company. Premium collection is processed through the **Squad payment gateway**, with funds ultimately settled into the insurance company's bank account net of commission.

This PRD covers the **backend service only**: data model, API surface, payment/settlement architecture, roles & permissions, security, and non-functional requirements. No frontend, mobile app, or admin UI design is included.

### Primary objective
Let an insurance company's brokers collect premiums (individually or in bulk) without the operational/accounting overhead of reconciling many small payments — Insureflow centralizes collection and pays the insurer net of commission, in as few settlement transactions as practical, with a clean audit trail.

---

## 2. Goals

- Onboard insurance companies and their brokers with an admin-approval workflow.
- Allow brokers to create policyholders and generic insurance policies.
- Allow brokers to collect premiums — **single** or **bulk** — through Squad, with the broker debited once per action and the insurer settled net of commission.
- Track a three-way commission split (GTBank, Insureflow, Broker) per transaction, configurable and versioned.
- Provide a complete, immutable audit trail suitable for financial reconciliation and regulatory review.
- Support a 1:1 broker–insurer relationship today, structured so it can become many-to-many later without a schema rewrite.

## 2.1 Non-Goals (out of scope for this PRD)

- Underwriting, actuarial pricing, or risk scoring logic.
- Claims management.
- Frontend/UI of any kind (web, mobile, admin dashboard) — API only.
- Direct integration with insurer core systems (policy admin systems) — assumed out of scope unless raised later.
- Multi-currency support beyond NGN at launch (Squad also supports USD; flagged as a future option, not built now).

---

## 3. Definitions & Glossary

| Term | Meaning |
|---|---|
| **Insurer** | Insurance company tenant onboarded onto Insureflow. |
| **Broker** | Entity onboarded by/under an Insurer, who manages policyholders and collects premiums. |
| **User** | A policyholder — created and managed by a broker, not a system login account by default (see §6.4). |
| **Policy** | A generic insurance contract record tied to a User, owned by a Broker/Insurer. |
| **Premium Installment** | One scheduled/due payment against a policy (supports recurring premiums). |
| **Single Payment** | One installment paid in one transaction. |
| **Bulk Payment** | Multiple installments (across one or more policies, same broker/insurer) paid in a single broker debit and a single insurer settlement. |
| **Settlement** | The transfer of net premium funds from Insureflow's Squad wallet to the Insurer's bank account. |
| **Commission Split** | The percentage of each premium retained by GTBank, Insureflow, and the Broker. |
| **VA** | Squad Virtual Account. |

---

## 4. Roles & Permissions

| Role | Scope | Key Permissions |
|---|---|---|
| **Insureflow Admin** | Platform-wide | Approve/reject insurer & broker onboarding; manage global commission defaults; view all tenants' data for support/compliance; suspend tenants. |
| **Insurance Company Admin** | Own tenant | Approve/manage own brokers; configure broker-level commission (where applicable); view all policies/payments under their tenant; send payment reminders to brokers; view settlement history. |
| **Broker Admin** | Own broker org | Manage broker staff users; onboard users/policies; initiate single/bulk payments; view own broker's transaction history. |
| **Broker Staff** | Own broker org | Create users/policies; initiate payments (no staff management). |

Permissions are enforced via RBAC + tenant scoping (see §11.2). A full permission matrix (resource × action × role) will be maintained as a living table in the repo (`docs/rbac-matrix.md`) rather than duplicated here, but the categories above define the ceiling for each role.

---

## 5. System Architecture Overview

```
                    ┌───────────────────────┐
                    │   FastAPI Application │
                    │  (Pydantic schemas,   │
                    │   RBAC middleware)     │
                    └──────────┬────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
 ┌──────▼──────┐       ┌───────▼───────┐      ┌───────▼────────┐
 │  PostgreSQL  │       │ Redis + Celery │      │  Squad API      │
 │ (system of   │       │ (webhooks,     │      │ (collection +   │
 │  record)     │       │ reminders,     │      │  transfer/      │
 │              │       │ settlement     │      │  payout rails)  │
 │              │       │ jobs, retries) │      │                 │
 └──────────────┘       └────────────────┘      └─────────────────┘
```

- **FastAPI + Pydantic**: request/response validation, OpenAPI docs generated for free, dependency-injected auth/RBAC/tenant context.
- **PostgreSQL**: single source of truth; row-level tenant scoping; double-entry ledger for financial integrity (see §8.7).
- **Redis + Celery**: async processing of Squad webhooks, scheduled settlement runs, reconciliation jobs, and broker payment reminders.
- **Squad API**: used for (a) premium **collection** (Direct API integration — server-to-server charge, no hosted checkout redirect, per your preference) and (b) **payout/transfer** to insurer bank accounts net of commission.

---

## 6. Multi-Tenancy Model

- Insureflow is multi-tenant at the **Insurance Company** level. Each insurer's data (brokers, users, policies, payments) is logically isolated.
- **Insureflow Admin** is the only role with cross-tenant visibility.
- Tenant scoping is enforced at the service layer on every query (`insurance_company_id` filter), with Postgres Row-Level Security as a defense-in-depth option (see §11.2).

### 6.1 Broker–Insurer relationship (1:1 today, extensible)

Per your direction, a broker belongs to exactly **one** insurer at launch. Rather than a simple FK on `brokers.insurance_company_id`, this is modeled as a separate **assignment table**:

```
broker_insurer_assignments
  id, broker_id, insurance_company_id, is_active, assigned_at, ended_at
```

A **partial unique constraint** (`UNIQUE (broker_id) WHERE is_active = true`) enforces "one active insurer per broker" today. To support many-to-many later, you only need to **drop that constraint** — no schema migration of core tables (`brokers`, `policies`, `payments`) is required, since they already reference the assignment relationship rather than assuming a single hardcoded FK. This is the extensibility hook you asked for.

### 6.2 Onboarding & approval

- Insurance Company and Broker onboarding both capture **basic KYB fields** at launch (legal name, registration number, contact details, address) — extensible via a `kyb_metadata JSONB` column so insurer-specific or broker-specific fields can be added later without migrations.
- Both onboarding flows require **manual approval by an Insureflow Admin** before the tenant/broker becomes active (`status: pending → approved/rejected`). Rejection requires a reason (stored, audit-logged).

### 6.3 Policies are generic at launch

`policies.policy_type` is a free-text/enum-ready field seeded with a single value (`GENERIC`) so it can be enumerated into real product types (motor, health, life, etc.) later without a breaking change — consumers should treat it as an open string, not assume a fixed enum.

### 6.4 Users (policyholders)

Users are created and managed **by brokers**; they are data records, not authenticated platform accounts, unless you later want a self-service policyholder portal (explicitly out of scope now — flagged in §13).

---

## 7. Recurring Premiums & Reminders

- Premiums are **recurring** (per the policy's `premium_frequency`), but payment is **never auto-debited**. Each due date generates a `premium_installment` row (`status: due`); the broker manually triggers payment for it (or includes it in a bulk batch).
- Insurers can send a **payment reminder** directly to a broker for a specific policy/installment (`POST /reminders`). Reminders are tracked (sent_by, sent_at, channel, status) so insurers can see whether/when a broker was nudged. Channel at launch: **email** (in-app/SMS as a fast-follow, not built now).
- A scheduled Celery job flags overdue installments (`due_date < today AND status = due` → `overdue`) for visibility; it does not auto-charge anything.

---

## 8. Payments: Single & Bulk

A single API surface handles both cases — bulk is modeled as "many installments, one broker debit, one insurer settlement," not as repeated single calls.

### 8.1 Core principle (per your requirement)

> Brokers are debited **once** per payment action (single or bulk). Insurers are settled **once** per payment action, net of commission — this is the core simplification Insureflow provides over paying each policy separately.

### 8.2 Single payment flow

1. Broker calls `POST /payments` with one `premium_installment_id`.
2. Insureflow creates a `Payment` record (`status: initiated`) with a unique idempotency key and transaction reference.
3. Insureflow calls Squad's Direct API charge/initiate endpoint for the premium amount.
4. Squad processes the charge (card/bank/transfer/USSD) and sends a webhook (`charge_successful` / failed) signed via `x-squad-encrypted-body`.
5. On verified success: `Payment.status = success`, `premium_installment.status = paid`, ledger entries created (§8.7), and the amount is queued for settlement to the insurer (§8.6).
6. Insureflow **independently re-verifies** the transaction via Squad's transaction query endpoint before trusting the webhook alone (defense against spoofed/duplicate callbacks) — see §11.2.

### 8.3 Bulk payment flow

1. Broker calls `POST /payments/bulk` with a list of `premium_installment_id`s (any number of policies/users, all under the broker's single insurer — consistent with the 1:1 model).
2. Insureflow validates: all installments belong to this broker, are unpaid, and sums the total.
3. Insureflow creates one `PaymentBatch` (status: initiated) + one `PaymentBatchItem` per installment, and **one** Squad charge for the **total batch amount**.
4. On webhook/verified success: the batch is marked `success`, and a fan-out step marks every linked installment as `paid` and writes one ledger entry per item (so per-policy accounting is preserved even though the broker debit was singular).
5. One settlement transfer is queued for the insurer, equal to the batch total net of commission — i.e., the insurer receives **one** payout for the whole batch, not one per policy.
6. **Partial failure handling**: because Squad charges the batch as a single transaction, it is atomic from a collection standpoint (it either succeeds or fails as a whole). If it fails, no installments are marked paid and the broker can retry with a corrected batch.

### 8.3.1 Maximum batch size

`POST /payments/bulk` is capped at **500 installments per batch** (`MAX_BULK_PAYMENT_ITEMS = 500`, configurable). Requests exceeding this are rejected with a 422 before any Squad call is made.

This is **not** a Squad-imposed limit — bulk collection is a single `transaction/initiate` call regardless of batch size, so Squad's rate limits don't bottleneck this endpoint at all (that constraint applies to the settlement sweep in §8.6, not here). The 500 cap exists purely to bound our own request payload size, the `PaymentBatchItem` insert cost, and the fan-out cost of marking every installment paid and posting a ledger entry per item on success. 500 is a starting assumption, not a measured number — it should be confirmed (and adjusted up or down) with load testing once the service is built, per your direction.

### 8.4 Idempotency

- Every payment-initiating endpoint (`POST /payments`, `POST /payments/bulk`) requires an `Idempotency-Key` header. Replaying the same key returns the original result rather than creating a duplicate charge.
- Squad transaction/transfer references are generated server-side as `{merchant_id}_{uuid}` to guarantee uniqueness, per Squad's requirement that transfer references be unique and merchant-prefixed.

### 8.5 Webhook handling

- All Squad webhooks land on a single endpoint, are persisted verbatim (`webhook_events` table) before processing, and are validated against the `x-squad-encrypted-body` signature header. Unsigned/invalid payloads are logged and rejected, never processed.
- Processing is idempotent and queued via Celery — a `transaction_ref` + `event_type` combination is only ever applied once, regardless of how many times Squad retries delivery.
- A scheduled **reconciliation job** periodically cross-checks Insureflow's "success" payments/transfers against Squad's "Query All Transactions" / "Get All Transfers" / "Re-query Transfer" endpoints to catch any missed or out-of-order webhooks.

### 8.6 Settlement to the insurer

- Each insurer's verified bank account (looked up and confirmed via Squad's Account Lookup API at onboarding time, stored as `account_name`/`account_number`/`bank_code`) is the destination for settlement payouts via Squad's Transfer API.
- **Open decision (flagged for product/finance sign-off, not yet built):** settlement can run in one of two modes, configurable per insurer:
  - **Real-time**: a payout fires immediately after each successful payment/batch, net of commission. Matches "insurer paid in one go" most literally for bulk, but means many small transfers for single payments.
  - **Scheduled net settlement**: payouts are swept on a schedule (e.g., daily) per insurer, summing all successful payments/batches since the last sweep into one transfer. Reduces transfer volume/fees, still gives the insurer one clean payout to reconcile against an Insureflow-generated statement.
  - Bulk payments, per your explicit requirement, **always** settle as one payout per batch regardless of mode. The open question only concerns single payments. Default assumption for MVP: **real-time** (simplest to build and verify first), with scheduled settlement as a near-term iteration.
- Transfer status is verified via Squad's re-query endpoint before being marked final; per Squad's guidance, a failed/timed-out transfer is **never retried with the same reference** — a new payout attempt uses a new reference, and the failure is audit-logged.

### 8.7 Ledger (double-entry) for accounting integrity

Given the transaction volumes involved, premium collection is **not** modeled as simple balance fields — it's modeled as double-entry ledger postings, so every naira is traceable and the books always balance:

| Account type | Represents |
|---|---|
| `BROKER_CLEARING` | Funds received from a broker, pending split. |
| `GTBANK_REVENUE` | GTBank's commission share. |
| `INSUREFLOW_REVENUE` | Insureflow's commission share. |
| `BROKER_COMMISSION` | Broker's commission share (if applicable — see §9). |
| `INSURER_PAYABLE` | Net amount owed to the insurer, pending settlement. |
| `INSURER_SETTLED` | Net amount paid out to the insurer (clears `INSURER_PAYABLE`). |

A successful `Payment`/`PaymentBatch` posts a balanced set of ledger entries; a `SettlementPayout` posts the entries that clear `INSURER_PAYABLE` into `INSURER_SETTLED`. This gives a complete, queryable trail per policy, per broker, per insurer, and platform-wide — which is the actual mechanism behind "simplifying their accounting."

---

## 9. Commission Engine

Three parties split every transaction: **GTBank**, **Insureflow**, and the **Broker**. This is explicitly under review, so it's built as **versioned, configurable data — not hardcoded constants**:

```
commission_configs
  id, scope ('global' | 'insurance_company' | 'broker'),
  insurance_company_id (nullable), broker_id (nullable),
  gtbank_rate_bps, insureflow_rate_bps, broker_rate_bps (nullable),
  effective_from, effective_to (nullable),
  created_by, created_at
```

- Rates are stored in **basis points** (integers), never as floats, to avoid rounding/precision bugs at scale.
- The applicable config for a transaction is resolved at the **most specific scope available** (broker → insurance_company → global) and **locked in at the time of payment** via a reference on the `Payment`/`PaymentBatch` row — so a later rate change never retroactively alters historical transactions.
- Broker commission rate is **nullable and insurer-settable**, since per your note it may be negotiated internally by each insurance firm rather than fixed platform-wide.
- Changing a rate never edits a row in place; it closes the current config (`effective_to = now`) and inserts a new one — preserving full history for audit.

> **Confirmed rates:** GTBank 0.5% (50 bps), Insureflow 0.5% (50 bps) — total platform take of 1% per transaction, before any broker commission. These are the defaults for the global `commission_configs` row; broker-level rates remain insurer-set and are not defaulted here.

---

## 10. API Surface (high-level)

Full request/response schemas belong in the OpenAPI spec generated by FastAPI; this is the resource-level shape for review.

| Group | Endpoints (indicative) |
|---|---|
| Auth | `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` |
| Insureflow Admin | `GET /admin/insurance-companies`, `PATCH /admin/insurance-companies/{id}/approve`, `PATCH /admin/insurance-companies/{id}/reject`, `GET /admin/brokers`, `PATCH /admin/brokers/{id}/approve`, `PATCH /admin/commission-configs`, `GET /admin/audit-logs` |
| Insurance Companies | `POST /insurance-companies` (onboard, pending), `GET /insurance-companies/{id}`, `PATCH /insurance-companies/{id}`, `GET /insurance-companies/{id}/brokers`, `GET /insurance-companies/{id}/settlements` |
| Brokers | `POST /brokers` (onboard, pending), `GET /brokers/{id}`, `PATCH /brokers/{id}`, `POST /brokers/{id}/staff`, `GET /brokers/{id}/transactions` |
| Users (policyholders) | `POST /users`, `GET /users/{id}`, `GET /users?broker_id=` |
| Policies | `POST /policies`, `GET /policies/{id}`, `GET /policies?user_id=` |
| Premium Installments | `GET /policies/{id}/installments`, `GET /installments?status=overdue` |
| Reminders | `POST /reminders` (insurer → broker, per policy/installment), `GET /reminders?broker_id=` |
| Payments | `POST /payments` (single), `GET /payments/{id}`, `GET /payments?broker_id=` |
| Bulk Payments | `POST /payments/bulk`, `GET /payments/bulk/{batch_id}` |
| Settlements | `GET /settlements`, `GET /settlements/{id}` (Insureflow Admin + relevant Insurer) |
| Webhooks | `POST /webhooks/squad` (internal, not user-facing) |
| Commission | `GET /commission-configs`, `POST /commission-configs` (Insureflow Admin; broker-scoped writes restricted to Insurance Company Admin) |

---

## 11. Security & Compliance

Given the transaction volumes expected (potentially billions of naira), security is treated as a first-class requirement, not an afterthought.

### 11.1 AuthN/AuthZ

- JWT-based auth (short-lived access token + refresh token), scoped to a single tenant context per token (Insureflow Admin tokens excepted).
- RBAC enforced via FastAPI dependencies on every route; role × resource permissions defined centrally, not scattered across handlers.

### 11.2 Tenant isolation

- Every query is scoped by `insurance_company_id` at the service/repository layer.
- **Recommended hardening**: Postgres Row-Level Security (RLS) policies as a second, database-enforced layer — so a bug in application-layer scoping can't leak cross-tenant data. Flagged for inclusion before go-live, not strictly MVP-blocking.

### 11.3 Payments-specific security

- Mandatory idempotency keys on all payment-initiating endpoints.
- Webhook signature verification (`x-squad-encrypted-body`) on every inbound webhook; invalid signatures are rejected and logged, never processed.
- Independent re-verification of transaction status via Squad's query/re-query endpoints before trusting any webhook for a financial state change.
- Squad API keys (sandbox/live) stored in a secrets manager (e.g., cloud KMS/Vault), never in source control or plain environment files committed to the repo; rotated on a defined schedule.
- All monetary amounts stored as integers in the lowest currency unit (kobo), matching Squad's convention, never as floats.

### 11.4 Data protection

- PII and KYB-sensitive fields (identification numbers, bank account details) encrypted at rest (column-level encryption / `pgcrypto`).
- TLS enforced everywhere; HSTS on public endpoints.

### 11.5 Audit logging

- An **immutable, insert-only** `audit_logs` table records every state-changing action: who (actor), what (action/entity), before/after state, IP, timestamp. Covers onboarding approvals, commission config changes, and every financial state transition.
- Audit logs are retained indefinitely (or per regulatory retention requirement, to be confirmed) and are queryable by Insureflow Admins for compliance review.

### 11.6 Rate limiting & abuse prevention

- Per-broker and per-IP rate limits on payment-initiating endpoints.
- Anomaly flags (e.g., unusual bulk batch size/value vs. broker history) logged for manual review — not blocking by default, but visible to Insureflow Admins.

---

## 12. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Scale | Tens of insurers, hundreds of brokers at launch; designed to scale to thousands of brokers without re-architecture. |
| Throughput | High transaction volume (potentially billions of NGN in cumulative value); payment paths must be async-safe and horizontally scalable (stateless API + Celery workers). |
| Availability | Target 99.9% for the API; payment/webhook paths designed to degrade gracefully (queue and retry) rather than drop data during Squad or downstream outages. |
| Observability | Structured logging (correlation/trace IDs across request → webhook → settlement), metrics on payment success/failure rates, alerting on failed settlements or webhook signature failures. |
| Backups/DR | Postgres point-in-time recovery; documented RPO/RTO targets (to be confirmed with infra team). |
| Environments | Strict separation of sandbox vs. live Squad credentials per environment; no live keys in non-production environments. |

---

## 13. Testing & QA Strategy

This PRD does not contain detailed test cases — those belong to engineering/QA during implementation — but given real money moves through this system, the following categories are treated as required, not optional, and the financial-invariant tests are a hard CI gate.

| Category | What it covers | Why it matters here |
|---|---|---|
| Unit tests | Commission split math (bps rounding, effective-date resolution), ledger entry generation, RBAC permission checks, Pydantic schema edge cases | Smallest, fastest layer to catch arithmetic and validation bugs before they touch money |
| Integration tests (Squad sandbox) | Collection (`transaction/initiate`), payout (`payout/transfer`, `account/lookup`), webhook signature validation (valid/invalid/replayed) | Confirms our assumptions about Squad's actual behavior, not just our mocks of it |
| Idempotency tests | Duplicate `Idempotency-Key` on `/payments` and `/payments/bulk`; duplicate webhook delivery for the same `transaction_ref` | Prevents double-charging a broker or double-crediting a ledger entry |
| End-to-end flow tests | Full single payment (initiate → webhook → ledger → settlement) and full bulk payment (batch → one charge → fan-out → one settlement), plus failure paths (declined charge, missing webhook caught by reconciliation) | Validates the actual broker-facing promise: one debit, one settlement |
| Concurrency tests | Two simultaneous bulk requests touching overlapping installments; concurrent webhook deliveries for the same transaction | Race conditions are the most likely source of double-payment bugs at scale |
| Multi-tenancy & RBAC tests | Broker A can never read/act on Insurer B's data; every role boundary in §4 enforced | Tenant leakage in a financial system is a regulatory and trust failure, not just a bug |
| **Financial correctness invariants** | Ledger debits always equal credits after every operation; commission splits always sum exactly back to the gross amount (see rounding note below) | Treated as a hard CI gate — a failing invariant test blocks merge, full stop |
| Load tests | Validates the 500-item bulk cap (§8.3.1) and settlement-sweep concurrency limits (§8.6) against real measured latency, not assumptions | Turns last week's estimates into measured numbers before go-live |
| Security tests | Webhook signature tampering, replay attacks, JWT expiry/refresh edge cases, rate-limit enforcement | Matches the "security first" expectation set in §11 |

### 13.1 Open item surfaced by this section: kobo-level rounding

Splitting a premium into GTBank/Insureflow/broker/insurer shares by basis points won't always divide evenly into whole kobo (the smallest unit Squad and our ledger both use). A rounding rule needs to be defined — e.g., the remainder kobo is absorbed into `INSURER_PAYABLE` rather than GTBank's or Insureflow's share — and a corresponding test must assert that every split sums **exactly** back to the original gross amount, with zero drift. This is flagged here rather than answered, since it's a finance/product decision, not an engineering default to assume silently.

---

## 14. Assumptions & Open Questions

1. **Commission rates** — confirmed: GTBank 0.5%, Insureflow 0.5%, total 1% (see §9). Broker commission rate remains insurer-set and unconfirmed.
2. **Settlement mode for single payments** — real-time vs. scheduled net settlement (§8.6) is a business decision, not yet made; MVP assumes real-time.
3. **Broker commission mechanism** — confirmed to be insurer-set and possibly variable; exact UI/workflow for insurers to set/change this is not yet specified (assumed: an endpoint restricted to Insurance Company Admin, versioned like all commission configs).
4. **Reminder channels** — email assumed for MVP; SMS/in-app/push not yet scoped.
5. **Policy type enumeration** — generic for now; timeline for introducing real product types (motor, health, life, etc.) not yet defined.
6. **Many-to-many broker–insurer** — schema is ready for it (§6.1), but no timeline requested yet; flagging only so it isn't assumed to be a current feature.
7. **Currency** — NGN only assumed for MVP; Squad supports USD as well if multi-currency becomes a requirement.
8. **Regulatory retention period** for audit logs/financial records — to be confirmed (e.g., NAICOM or other applicable guidance) so retention policy can be set correctly rather than guessed.
9. **Bulk batch size cap** — set at 500 items/batch (§8.3.1) as a starting assumption; to be validated (and adjusted if needed) with load testing once the service is built.

---

## 15. Appendix: Squad API Surfaces Used

| Capability | Squad endpoint (sandbox base shown) |
|---|---|
| Collection (premium charge) | `POST /transaction/initiate` (Direct API) |
| Transaction verification | `GET /transaction` (query), transaction verify endpoint |
| Webhook (charge result) | Inbound POST to Insureflow, signed via `x-squad-encrypted-body` |
| Account lookup (insurer bank account) | `POST /payout/account/lookup` |
| Settlement payout | `POST /payout/transfer` |
| Payout status check | `POST /payout/requery` |
| All transfers (reconciliation) | `GET /payout/list` |

Full reference: https://docs.squadco.com/

---

*End of document. This is a v0.1 draft intended to drive architecture/data-model review — flagged assumptions in §14 should be resolved before implementation begins.*
