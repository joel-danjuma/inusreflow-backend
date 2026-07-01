import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.broker import Broker
from app.models.commission_config import CommissionConfig
from app.models.insurance_company import InsuranceCompany
from app.models.payment_batch import PaymentBatch
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Role
from app.services.anomaly_service import flag_if_anomalous_batch


async def _seed_broker_and_config(
    db_session: AsyncSession,
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID]:
    company = InsuranceCompany(name="Anomaly Co", contact_email=f"{uuid.uuid4()}@example.com")
    broker = Broker(name="Anomaly Brokers", contact_email=f"{uuid.uuid4()}@example.com")
    db_session.add_all([company, broker])
    await db_session.flush()

    actor = PlatformUser(
        email=f"{uuid.uuid4()}@example.com",
        role=Role.BROKER_ADMIN.value,
        broker_id=broker.id,
        is_active=True,
    )
    db_session.add(actor)
    await db_session.flush()

    config = CommissionConfig(
        scope="broker", broker_id=broker.id, gtbank_rate_bps=50, insureflow_rate_bps=50
    )
    db_session.add(config)
    await db_session.flush()

    return broker.id, company.id, actor.id, config.id


def _make_batch(
    *,
    broker_id: uuid.UUID,
    insurance_company_id: uuid.UUID,
    initiated_by: uuid.UUID,
    commission_config_id: uuid.UUID,
    item_count: int,
    total_amount_kobo: int,
) -> PaymentBatch:
    return PaymentBatch(
        broker_id=broker_id,
        insurance_company_id=insurance_company_id,
        initiated_by=initiated_by,
        commission_config_id=commission_config_id,
        total_amount_kobo=total_amount_kobo,
        item_count=item_count,
        status="initiated",
        squad_transaction_ref=f"ref_{uuid.uuid4()}",
    )


async def test_no_flag_with_insufficient_trailing_history(db_session: AsyncSession) -> None:
    """anomaly_min_history_batches defaults to 3 -- a broker's first couple
    of batches have no real baseline to compare against, so even a huge
    batch must not be flagged yet.
    """
    broker_id, company_id, actor_id, config_id = await _seed_broker_and_config(db_session)

    db_session.add(
        _make_batch(
            broker_id=broker_id,
            insurance_company_id=company_id,
            initiated_by=actor_id,
            commission_config_id=config_id,
            item_count=2,
            total_amount_kobo=10_000,
        )
    )
    await db_session.flush()

    huge_batch = _make_batch(
        broker_id=broker_id,
        insurance_company_id=company_id,
        initiated_by=actor_id,
        commission_config_id=config_id,
        item_count=200,
        total_amount_kobo=10_000_000,
    )
    db_session.add(huge_batch)
    await db_session.flush()

    await flag_if_anomalous_batch(db_session, huge_batch)

    flags = (
        await db_session.scalars(
            select(AuditLog).where(AuditLog.action == "payment_batch.anomaly_flagged")
        )
    ).all()
    assert flags == []


async def test_flags_a_batch_that_dwarfs_the_brokers_trailing_average(
    db_session: AsyncSession,
) -> None:
    broker_id, company_id, actor_id, config_id = await _seed_broker_and_config(db_session)

    for _ in range(3):
        db_session.add(
            _make_batch(
                broker_id=broker_id,
                insurance_company_id=company_id,
                initiated_by=actor_id,
                commission_config_id=config_id,
                item_count=2,
                total_amount_kobo=10_000,
            )
        )
    await db_session.flush()

    outlier_batch = _make_batch(
        broker_id=broker_id,
        insurance_company_id=company_id,
        initiated_by=actor_id,
        commission_config_id=config_id,
        item_count=50,
        total_amount_kobo=500_000,
    )
    db_session.add(outlier_batch)
    await db_session.flush()

    await flag_if_anomalous_batch(db_session, outlier_batch)

    flag = await db_session.scalar(
        select(AuditLog).where(
            AuditLog.action == "payment_batch.anomaly_flagged",
            AuditLog.entity_id == outlier_batch.id,
        )
    )
    assert flag is not None
    assert flag.after_state is not None
    assert len(flag.after_state["reasons"]) == 2


async def test_does_not_flag_a_batch_within_normal_range(db_session: AsyncSession) -> None:
    broker_id, company_id, actor_id, config_id = await _seed_broker_and_config(db_session)

    for _ in range(3):
        db_session.add(
            _make_batch(
                broker_id=broker_id,
                insurance_company_id=company_id,
                initiated_by=actor_id,
                commission_config_id=config_id,
                item_count=2,
                total_amount_kobo=10_000,
            )
        )
    await db_session.flush()

    normal_batch = _make_batch(
        broker_id=broker_id,
        insurance_company_id=company_id,
        initiated_by=actor_id,
        commission_config_id=config_id,
        item_count=3,
        total_amount_kobo=15_000,
    )
    db_session.add(normal_batch)
    await db_session.flush()

    await flag_if_anomalous_batch(db_session, normal_batch)

    flag = await db_session.scalar(
        select(AuditLog).where(
            AuditLog.action == "payment_batch.anomaly_flagged",
            AuditLog.entity_id == normal_batch.id,
        )
    )
    assert flag is None
