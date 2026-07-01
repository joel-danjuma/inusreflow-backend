from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class DynamicVirtualAccount:
    """Squad's response to initiate-dynamic-virtual-account. expected_amount is
    intentionally not parsed into kobo here -- it's Naira-formatted on the
    wire (e.g. "100.00"), unlike the request's amount_kobo field, and we
    never need it: our own Payment.amount_kobo is the source of truth.
    """

    account_number: str
    account_name: str
    bank: str
    expires_at: datetime
    transaction_reference: str
    currency: str
    raw: dict[str, Any]


@dataclass(frozen=True)
class DynamicVirtualAccountTransaction:
    """Result of independently re-querying a VA transaction (never trust the
    webhook body alone -- CLAUDE.md). transaction_status is one of SUCCESS /
    MISMATCH / EXPIRED. amount_received is kept as the raw wire string
    (unit not independently confirmed) since the success/failure decision
    rests on transaction_status alone, per docs/adr/0004.
    """

    transaction_reference: str
    transaction_status: str
    merchant_reference: str
    amount_received: str | None
    raw: dict[str, Any]


@dataclass(frozen=True)
class PayoutAccountLookup:
    account_number: str
    account_name: str
    raw: dict[str, Any]


@dataclass(frozen=True)
class TransferResult:
    transaction_reference: str
    status: str
    raw: dict[str, Any]


@dataclass(frozen=True)
class TransferStatusResult:
    """Result of independently re-querying (POST /payout/requery) or listing
    (GET /payout/list) a transfer -- the initiate_transfer response alone is
    never trusted as final (PRD §8.6). transaction_status is Squad's own
    value: success / pending / failed / reversed.
    """

    transaction_reference: str
    transaction_status: str
    raw: dict[str, Any]
