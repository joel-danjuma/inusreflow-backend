# ADR 0003: Settlement mode for single payments

## Status
Accepted for this build — real-time settlement.

## Context
PRD §8.6/§14.2 leaves single-payment settlement mode as an open business decision: real-time-per-payment vs. scheduled net settlement (e.g. daily sweep). Bulk payments are unconditional — always one payout per batch, regardless of mode.

## Decision
Single payments settle in real time: a payout fires immediately after each successful payment, net of commission. This matches the PRD's stated MVP default and is simplest to build and verify first.

`insurance_companies.settlement_mode` (`real_time` | `scheduled`) is reserved in the schema so a future per-insurer scheduled-sweep mode can be added without a schema change — but scheduled settlement is **not built** in this codebase yet.

## Consequences
- Many small transfers for insurers with high single-payment volume, rather than one consolidated daily payout.
- If/when scheduled settlement is requested, it's additive: a new settlement-sweep job reading `settlement_mode`, not a rework of the real-time path.
