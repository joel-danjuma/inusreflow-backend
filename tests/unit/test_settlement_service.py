import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.models.insurance_company import InsuranceCompany
from app.services import settlement_service
from tests.fakes import FakeSquadClient

_MERCHANT_ID = "test-merchant"
_BANK_CODE = "058"
_ACCOUNT_NUMBER = "0123456789"


async def _seed_insurance_company(
    db_session: AsyncSession, *, with_bank_details: bool = True
) -> InsuranceCompany:
    company = InsuranceCompany(
        name="Settlement Test Insurance",
        contact_email=f"{uuid.uuid4()}@example.com",
        settlement_bank_code=_BANK_CODE if with_bank_details else None,
        settlement_account_number=_ACCOUNT_NUMBER if with_bank_details else None,
        settlement_account_name="Settlement Test Insurance Ltd" if with_bank_details else None,
    )
    db_session.add(company)
    await db_session.flush()
    return company


async def test_settle_payment_resolves_to_success_when_requery_confirms_success(
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
    assert payout.attempt_number == 1
    assert payout.previous_attempt_id is None


async def test_settle_payment_records_pending_when_requery_is_ambiguous(
    db_session: AsyncSession,
) -> None:
    """initiate_transfer's own response is never the final word (PRD §8.6) --
    settle_payment must independently requery the transfer ref before
    deciding the outcome, and a still-ambiguous requery result is PENDING,
    not guessed into success.
    """
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
    assert len(fake.transfers) == 1


async def test_settle_payment_marks_failed_when_requery_reports_reversed(
    db_session: AsyncSession,
) -> None:
    company = await _seed_insurance_company(db_session)
    fake = FakeSquadClient()
    fake.simulate_next_transfer_status(status="reversed")

    payout = await settlement_service.settle_payment(
        db_session,
        insurance_company=company,
        source_type="payment",
        source_id=uuid.uuid4(),
        amount_kobo=10_000,
        squad_client=fake,
        merchant_id=_MERCHANT_ID,
    )

    assert payout.status == "failed"
    assert payout.failure_reason is not None
    assert "reversed" in payout.failure_reason


async def test_settle_payment_fails_closed_without_settlement_bank_details(
    db_session: AsyncSession,
) -> None:
    company = await _seed_insurance_company(db_session, with_bank_details=False)
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

    assert payout.status == "failed"
    assert fake.transfers == []


async def test_retry_failed_settlement_mints_fresh_ref_and_chains_attempt(
    db_session: AsyncSession,
) -> None:
    company = await _seed_insurance_company(db_session, with_bank_details=False)
    fake = FakeSquadClient()

    first_attempt = await settlement_service.settle_payment(
        db_session,
        insurance_company=company,
        source_type="payment",
        source_id=uuid.uuid4(),
        amount_kobo=10_000,
        squad_client=fake,
        merchant_id=_MERCHANT_ID,
    )
    assert first_attempt.status == "failed"

    # Bank details get configured after the original failure.
    company.settlement_bank_code = _BANK_CODE
    company.settlement_account_number = _ACCOUNT_NUMBER
    company.settlement_account_name = "Settlement Test Insurance Ltd"
    await db_session.flush()

    retried = await settlement_service.retry_failed_settlement(
        db_session,
        first_attempt,
        insurance_company=company,
        squad_client=fake,
        merchant_id=_MERCHANT_ID,
    )

    assert retried.status == "success"
    assert retried.attempt_number == 2
    assert retried.previous_attempt_id == first_attempt.id
    assert retried.squad_transfer_ref != first_attempt.squad_transfer_ref


async def test_retry_failed_settlement_rejects_a_non_failed_payout(
    db_session: AsyncSession,
) -> None:
    company = await _seed_insurance_company(db_session)
    fake = FakeSquadClient()

    successful_payout = await settlement_service.settle_payment(
        db_session,
        insurance_company=company,
        source_type="payment",
        source_id=uuid.uuid4(),
        amount_kobo=10_000,
        squad_client=fake,
        merchant_id=_MERCHANT_ID,
    )
    assert successful_payout.status == "success"

    with pytest.raises(ConflictError, match="is not failed"):
        await settlement_service.retry_failed_settlement(
            db_session,
            successful_payout,
            insurance_company=company,
            squad_client=fake,
            merchant_id=_MERCHANT_ID,
        )


async def test_retry_failed_settlement_rejects_retrying_the_same_failed_attempt_twice(
    db_session: AsyncSession,
) -> None:
    """A failed payout's own row is never mutated by a retry -- it stays the
    historical record of that attempt -- so a second retry call against the
    same already-retried row must be rejected, not allowed to mint a second
    successful transfer for the same source_id.
    """
    company = await _seed_insurance_company(db_session, with_bank_details=False)
    fake = FakeSquadClient()

    first_attempt = await settlement_service.settle_payment(
        db_session,
        insurance_company=company,
        source_type="payment",
        source_id=uuid.uuid4(),
        amount_kobo=10_000,
        squad_client=fake,
        merchant_id=_MERCHANT_ID,
    )
    assert first_attempt.status == "failed"

    company.settlement_bank_code = _BANK_CODE
    company.settlement_account_number = _ACCOUNT_NUMBER
    company.settlement_account_name = "Settlement Test Insurance Ltd"
    await db_session.flush()

    retried = await settlement_service.retry_failed_settlement(
        db_session,
        first_attempt,
        insurance_company=company,
        squad_client=fake,
        merchant_id=_MERCHANT_ID,
    )
    assert retried.status == "success"

    with pytest.raises(ConflictError, match="already been retried"):
        await settlement_service.retry_failed_settlement(
            db_session,
            first_attempt,
            insurance_company=company,
            squad_client=fake,
            merchant_id=_MERCHANT_ID,
        )
    assert len(fake.transfers) == 1
