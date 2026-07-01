# ADR 0004: Premium collection via Squad Dynamic Virtual Accounts

## Status
Accepted, per explicit user direction.

## Context
PRD §8.2 describes `POST /payments` as a single broker-initiated call that results in a webhook-confirmed success, with no further interaction. Squad's real Direct API (card/bank charge) doesn't support that shape for a first-time charge: `transaction/initiate` returns an `auth_model` (e.g. `ValidateTOKEN` for GTBank accounts) and requires a second customer-entered-OTP call (`transaction/validate-payment`) before the charge resolves. There is no true one-shot pull-charge in Squad's API without a previously tokenized card/mandate, which the PRD doesn't describe setting up anywhere.

Confirmed (per user direction): all Insureflow payments are collected by **bank transfer into a Squad Dynamic Virtual Account**, not a pulled charge. This is a push model — the payer transfers funds in; no OTP is involved at any point.

## Decision
`POST /payments` (and `POST /payments/bulk`) create a Squad **Dynamic Virtual Account** scoped to the exact amount due (one installment, or one batch total) via `POST /virtual-account/initiate-dynamic-virtual-account`, and return the resulting account number/bank/expiry to the broker instead of a final payment status. The broker (or the policyholder, out of band) transfers the amount into that account.

Squad resolves the transfer asynchronously and calls back on the shared `POST /webhooks/squad` endpoint with one of three outcomes (`transaction_status`): `SUCCESS`, `MISMATCH` (wrong amount — Squad auto-refunds the sender), or `EXPIRED` (window closed with no transfer — also auto-refunded if a transfer arrived late). Only `SUCCESS`, independently re-verified via `GET /virtual-account/get-dynamic-virtual-account-transactions/:transaction_reference` before any financial state change, flips `Payment.status = success`, marks the installment paid, posts ledger entries, and queues settlement. `MISMATCH`/`EXPIRED` mark the payment failed; the broker retries via a fresh `POST /payments` call, which mints a new virtual account and a new `transaction_ref` — never reusing one, consistent with the existing failed-transfer-never-retried-with-same-reference rule.

No `beneficiary_account` is passed when creating the virtual account, so funds land in Insureflow's own Squad wallet rather than instant-settling straight to the insurer — Insureflow's own Transfer API call (§8.6) is what actually pays the insurer, net of commission, after the ledger split is posted. Passing the insurer's account as `beneficiary_account` would bypass the commission split and ledger entirely.

## Consequences
- `Payment` rows carry virtual-account fields (`squad_virtual_account_number`, `squad_virtual_account_bank`, `va_expires_at`) instead of a card/bank charge reference, and `status` includes `mismatch`/`expired` alongside `success`/`failed`.
- The `POST /payments` response is necessarily a "here's where to pay" instruction, not a final outcome — callers must poll `GET /payments/{id}` or wait for their own out-of-band confirmation that the transfer landed.
- Squad's webhook signature scheme for dynamic virtual accounts (`x-squad-encrypted-body`) is HMAC-SHA512, keyed with the merchant secret key, over the JSON-serialized object `{"transaction_reference": ..., "amount_received": ..., "merchant_reference": ...}` (in that key order), compared as lowercase hex — distinct from the pipe-delimited string this ADR originally assumed, and still less precisely documented (exact serialization whitespace/ordering) than the generic transaction webhook's whole-body HMAC-SHA512. Because every webhook is independently re-verified via the re-query endpoint before any financial state change (PRD §11.3), a signature-format correction (once observed against a live sandbox webhook) is a hardening fix, not a financial-integrity risk in the interim.
- Squad amounts are kobo throughout, including the Transfer API's `amount` field — it is typed as a string on the wire (e.g. `"10000"`) but the value is still kobo, not Naira; only the Dynamic VA *response*'s `expected_amount` field is Naira-formatted (e.g. `"100.00"`), and is never parsed back into our domain — it's stored verbatim in `raw_squad_response` for audit only, since our own `amount_kobo` on the `Payment` row is always the source of truth.
