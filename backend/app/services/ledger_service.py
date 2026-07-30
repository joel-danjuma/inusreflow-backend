import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ledger_account import LedgerAccount
from app.models.ledger_entry import LedgerEntry


@dataclass(frozen=True)
class LedgerPosting:
    ledger_account_id: uuid.UUID
    entry_type: Literal["debit", "credit"]
    amount_kobo: int
    reference_type: str
    reference_id: uuid.UUID


async def get_or_create_ledger_account(
    db: AsyncSession,
    *,
    account_type: str,
    insurance_company_id: uuid.UUID | None = None,
    broker_id: uuid.UUID | None = None,
) -> LedgerAccount:
    """Looks up the singleton ledger account for (account_type, scope),
    creating it on first use. Scope must match exactly one of the three
    partial unique indexes on ledger_accounts -- platform-wide (both ids
    NULL), per-broker, or per-insurer (broker_id takes precedence since
    BROKER_* account types are never also insurer-scoped).
    """
    stmt = select(LedgerAccount).where(LedgerAccount.account_type == account_type)
    if broker_id is not None:
        stmt = stmt.where(LedgerAccount.broker_id == broker_id)
    elif insurance_company_id is not None:
        stmt = stmt.where(
            LedgerAccount.insurance_company_id == insurance_company_id,
            LedgerAccount.broker_id.is_(None),
        )
    else:
        stmt = stmt.where(
            LedgerAccount.insurance_company_id.is_(None), LedgerAccount.broker_id.is_(None)
        )

    account = await db.scalar(stmt)
    if account is not None:
        return account

    account = LedgerAccount(
        account_type=account_type,
        insurance_company_id=insurance_company_id if broker_id is None else None,
        broker_id=broker_id,
    )
    db.add(account)
    await db.flush()
    return account


async def post_ledger_entries(
    db: AsyncSession,
    postings: Sequence[LedgerPosting],
    *,
    posting_group_id: uuid.UUID | None = None,
) -> uuid.UUID:
    """Inserts every posting in one atomic operation under a single
    posting_group_id, asserting sum(debits) == sum(credits) first -- the
    hard CI gate behind PRD §13's double-entry invariant. Callers must pass
    every entry for the operation in one call; a balance check over a
    partial set is meaningless.
    """
    if not postings:
        raise ValueError("post_ledger_entries requires at least one posting")

    group_id = posting_group_id or uuid.uuid4()

    debits = sum(p.amount_kobo for p in postings if p.entry_type == "debit")
    credits = sum(p.amount_kobo for p in postings if p.entry_type == "credit")
    if debits != credits:
        raise ValueError(
            f"unbalanced ledger posting group {group_id}: debits={debits} credits={credits}"
        )

    for posting in postings:
        db.add(
            LedgerEntry(
                ledger_account_id=posting.ledger_account_id,
                entry_type=posting.entry_type,
                amount_kobo=posting.amount_kobo,
                reference_type=posting.reference_type,
                reference_id=posting.reference_id,
                posting_group_id=group_id,
            )
        )
    await db.flush()
    return group_id
