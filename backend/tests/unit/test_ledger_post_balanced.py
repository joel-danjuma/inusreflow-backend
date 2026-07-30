import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.broker import Broker
from app.models.insurance_company import InsuranceCompany
from app.models.ledger_entry import LedgerEntry
from app.services.ledger_service import (
    LedgerPosting,
    get_or_create_ledger_account,
    post_ledger_entries,
)


async def _seed_broker_and_insurer(db_session: AsyncSession) -> tuple[Broker, InsuranceCompany]:
    broker = Broker(name="Ledger Test Brokers", contact_email=f"{uuid.uuid4()}@example.com")
    company = InsuranceCompany(
        name="Ledger Test Insurer", contact_email=f"{uuid.uuid4()}@example.com"
    )
    db_session.add_all([broker, company])
    await db_session.flush()
    return broker, company


async def test_balanced_posting_persists_and_sums_to_zero_drift(
    db_session: AsyncSession,
) -> None:
    broker, company = await _seed_broker_and_insurer(db_session)

    clearing = await get_or_create_ledger_account(
        db_session, account_type="BROKER_CLEARING", broker_id=broker.id
    )
    gtbank = await get_or_create_ledger_account(db_session, account_type="GTBANK_REVENUE")
    insureflow = await get_or_create_ledger_account(db_session, account_type="INSUREFLOW_REVENUE")
    insurer_payable = await get_or_create_ledger_account(
        db_session, account_type="INSURER_PAYABLE", insurance_company_id=company.id
    )

    reference_id = uuid.uuid4()
    group_id = await post_ledger_entries(
        db_session,
        [
            LedgerPosting(clearing.id, "debit", 100_000, "payment", reference_id),
            LedgerPosting(gtbank.id, "credit", 500, "payment", reference_id),
            LedgerPosting(insureflow.id, "credit", 500, "payment", reference_id),
            LedgerPosting(insurer_payable.id, "credit", 99_000, "payment", reference_id),
        ],
    )

    entries = await db_session.scalars(
        select(LedgerEntry).where(LedgerEntry.posting_group_id == group_id)
    )
    rows = entries.all()
    assert len(rows) == 4

    debits = sum(r.amount_kobo for r in rows if r.entry_type == "debit")
    credits = sum(r.amount_kobo for r in rows if r.entry_type == "credit")
    assert debits == credits == 100_000


async def test_unbalanced_posting_raises_and_persists_nothing(db_session: AsyncSession) -> None:
    broker, _ = await _seed_broker_and_insurer(db_session)
    clearing = await get_or_create_ledger_account(
        db_session, account_type="BROKER_CLEARING", broker_id=broker.id
    )
    gtbank = await get_or_create_ledger_account(db_session, account_type="GTBANK_REVENUE")

    reference_id = uuid.uuid4()
    with pytest.raises(ValueError, match="unbalanced"):
        await post_ledger_entries(
            db_session,
            [
                LedgerPosting(clearing.id, "debit", 100_000, "payment", reference_id),
                LedgerPosting(gtbank.id, "credit", 999, "payment", reference_id),
            ],
        )

    entries = await db_session.scalars(
        select(LedgerEntry).where(LedgerEntry.reference_id == reference_id)
    )
    assert entries.all() == []


async def test_get_or_create_ledger_account_is_idempotent_per_scope(
    db_session: AsyncSession,
) -> None:
    broker, _ = await _seed_broker_and_insurer(db_session)

    first = await get_or_create_ledger_account(
        db_session, account_type="BROKER_COMMISSION", broker_id=broker.id
    )
    second = await get_or_create_ledger_account(
        db_session, account_type="BROKER_COMMISSION", broker_id=broker.id
    )
    assert first.id == second.id


async def test_post_ledger_entries_requires_at_least_one_posting(
    db_session: AsyncSession,
) -> None:
    with pytest.raises(ValueError, match="at least one posting"):
        await post_ledger_entries(db_session, [])
