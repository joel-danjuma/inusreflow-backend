import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.broker import Broker
from app.models.insurance_company import InsuranceCompany
from app.models.policyholder import Policyholder

_IDENTIFICATION_NUMBER = "NIN-12345678"
_SETTLEMENT_ACCOUNT_NUMBER = "0123456789"


async def test_identification_number_round_trips_through_the_orm_but_is_ciphertext_at_rest(
    db_session: AsyncSession,
) -> None:
    """Writing/reading Policyholder.identification_number via the ORM must
    see plaintext (docs/adr/0007-pii-encryption.md) -- the encryption is
    invisible above the SQLAlchemy Core boundary -- while a raw SQL read of
    the same column never sees the plaintext, proving the encryption is
    real and not just a Python-side illusion.
    """
    company = InsuranceCompany(name="PII Test Co", contact_email=f"{uuid.uuid4()}@example.com")
    broker = Broker(name="PII Test Brokers", contact_email=f"{uuid.uuid4()}@example.com")
    db_session.add_all([company, broker])
    await db_session.flush()

    policyholder = Policyholder(
        broker_id=broker.id,
        insurance_company_id=company.id,
        full_name="Jane Doe",
        identification_number=_IDENTIFICATION_NUMBER,
    )
    db_session.add(policyholder)
    await db_session.flush()
    await db_session.refresh(policyholder)

    assert policyholder.identification_number == _IDENTIFICATION_NUMBER

    raw = await db_session.execute(
        text("SELECT identification_number FROM policyholders WHERE id = :id"),
        {"id": policyholder.id},
    )
    raw_value = raw.scalar()
    assert raw_value is not None
    assert _IDENTIFICATION_NUMBER.encode() not in raw_value


async def test_settlement_account_number_round_trips_through_the_orm_but_is_ciphertext_at_rest(
    db_session: AsyncSession,
) -> None:
    company = InsuranceCompany(name="PII Test Co Two", contact_email=f"{uuid.uuid4()}@example.com")
    company.settlement_account_number = _SETTLEMENT_ACCOUNT_NUMBER
    db_session.add(company)
    await db_session.flush()
    await db_session.refresh(company)

    assert company.settlement_account_number == _SETTLEMENT_ACCOUNT_NUMBER

    raw = await db_session.execute(
        text("SELECT settlement_account_number FROM insurance_companies WHERE id = :id"),
        {"id": company.id},
    )
    raw_value = raw.scalar()
    assert raw_value is not None
    assert _SETTLEMENT_ACCOUNT_NUMBER.encode() not in raw_value


async def test_a_null_identification_number_stays_null_through_encryption(
    db_session: AsyncSession,
) -> None:
    """pgp_sym_encrypt(NULL, key) must propagate NULL, not error or encode an
    empty ciphertext -- nullable PII fields are common (most policyholders
    won't have one captured at creation time).
    """
    company = InsuranceCompany(
        name="PII Test Co Three", contact_email=f"{uuid.uuid4()}@example.com"
    )
    broker = Broker(name="PII Test Brokers Three", contact_email=f"{uuid.uuid4()}@example.com")
    db_session.add_all([company, broker])
    await db_session.flush()

    policyholder = Policyholder(
        broker_id=broker.id,
        insurance_company_id=company.id,
        full_name="No ID Yet",
        identification_number=None,
    )
    db_session.add(policyholder)
    await db_session.flush()
    await db_session.refresh(policyholder)

    assert policyholder.identification_number is None
