from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StaticVirtualAccount:
    """Squad's response to POST /virtual-account/business. One VA is created
    per broker at approval time and reused permanently -- never one per payment
    (VA-limit constraint). customer_identifier is str(broker.id).
    """

    account_number: str
    account_name: str
    bank: str
    customer_identifier: str
    currency: str
    raw: dict[str, Any]


@dataclass(frozen=True)
class StaticVATransaction:
    """Result of independently re-querying a transaction via
    GET /transaction/verify/{squad_tx_ref} (never trust the webhook body alone
    -- CLAUDE.md). transaction_status is one of SUCCESS / FAILED / PENDING.
    squad_tx_ref is Squad's own transaction_reference from the SVA webhook
    payload (distinct from our internal squad_transaction_ref on Payment).
    """

    transaction_reference: str
    transaction_status: str
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
