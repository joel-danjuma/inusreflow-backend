# ADR 0001: Kobo-level rounding remainder

## Status
Provisional — pending finance/product sign-off (PRD §13.1 flags this explicitly as not to be silently assumed).

## Context
Splitting a gross premium into GTBank/Insureflow/broker/insurer shares by basis points does not always divide evenly into whole kobo. A rule is needed so every split sums exactly back to the gross amount with zero drift.

## Decision
Any leftover remainder kobo is allocated to `INSURER_PAYABLE`. GTBank/Insureflow/broker shares are always `floor(gross * rate_bps / 10_000)`; the insurer absorbs whatever's left.

Implemented as a swappable `RoundingStrategy` (`app/services/ledger/rounding.py`), selected via settings, so this rule can change without touching call sites in `commission_service`/`ledger_service`.

## Consequences
- The insurer's net amount may vary by a few kobo from a pure proportional split, always in the insurer's favor (never less than their proportional share).
- This must be revisited and confirmed with finance before being treated as final business logic — do not remove the "provisional" framing from code/docs until that sign-off happens.
