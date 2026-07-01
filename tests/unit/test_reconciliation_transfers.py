import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.insurance_company import InsuranceCompany
from app.services import reconciliation_service, settlement_service
from tests.fakes import FakeSquadClient

_MERCHANT_ID = "test-merchant"


async def _seed_insurance_company(db_session: AsyncSession) -> InsuranceCompany:
    company = InsuranceCompany(
        name="Reconciliation Test Insurance",
        contact_email=f"{uuid.uuid4()}@example.com",
        settlement_bank_code="058",
        settlement_account_number="0123456789",
        settlement_account_name="Reconciliation Test Insurance Ltd",
    )
    db_session.add(company)
    await db_session.flush()
    return company


async def test_reconcile_transfers_resolves_a_pending_payout_to_squads_reported_status(
    db_session: AsyncSession,
) -> None:
    company = await _seed_insurance_company(db_session)
    fake = FakeSquadClient()
    fake.simulate_next_transfer_status(status="pending")

    payout = await settlement_service.settle_payment(
        db_session,
        insurance_company=company,
        source_type="payment",
        source_id=uuid.uuid4(),
        amount_kobo=10_000,
        squad_client=fake,
        merchant_id=_MERCHANT_ID,
    )
    assert payout.status == "pending"

    fake.simulate_transfer_status(payout.squad_transfer_ref, status="success")
    result = await reconciliation_service.reconcile_transfers(db_session, squad_client=fake)

    assert result.payouts_resolved == 1
    assert result.mismatches_flagged == 0
    await db_session.refresh(payout)
    assert payout.status == "success"


async def test_reconcile_transfers_never_rewrites_an_already_terminal_payout(
    db_session: AsyncSession,
) -> None:
    """A payout we already recorded as success/failed is never silently
    mutated even if Squad's listing later disagrees (e.g. a reversal) --
    only flagged via an audit log entry for human review.
    """
    company = await _seed_insurance_company(db_session)
    fake = FakeSquadClient()

    payout = await settlement_service.settle_payment(
        db_session,
        insurance_company=company,
        source_type="payment",
        source_id=uuid.uuid4(),
        amount_kobo=10_000,
        squad_client=fake,
        merchant_id=_MERCHANT_ID,
    )
    assert payout.status == "success"

    fake.simulate_transfer_status(payout.squad_transfer_ref, status="reversed")
    result = await reconciliation_service.reconcile_transfers(db_session, squad_client=fake)

    assert result.mismatches_flagged == 1
    assert result.payouts_resolved == 0
    await db_session.refresh(payout)
    assert payout.status == "success"

    mismatch_log = await db_session.scalar(
        select(AuditLog).where(
            AuditLog.entity_id == payout.id,
            AuditLog.action == "settlement_payout.reconciliation_mismatch",
        )
    )
    assert mismatch_log is not None
    assert mismatch_log.after_state is not None
    assert mismatch_log.after_state["squad_transaction_status"] == "reversed"


async def test_reconcile_transfers_is_a_noop_for_a_payout_squad_still_agrees_with(
    db_session: AsyncSession,
) -> None:
    company = await _seed_insurance_company(db_session)
    fake = FakeSquadClient()

    payout = await settlement_service.settle_payment(
        db_session,
        insurance_company=company,
        source_type="payment",
        source_id=uuid.uuid4(),
        amount_kobo=10_000,
        squad_client=fake,
        merchant_id=_MERCHANT_ID,
    )
    assert payout.status == "success"

    result = await reconciliation_service.reconcile_transfers(db_session, squad_client=fake)

    assert result.payouts_resolved == 0
    assert result.mismatches_flagged == 0
