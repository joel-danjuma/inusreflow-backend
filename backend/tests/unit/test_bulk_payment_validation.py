import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, UnprocessableError
from app.models.broker import Broker
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Role
from app.services.bulk_payment_service import initiate_bulk_payment
from tests.fakes import FakeSquadClient

_MERCHANT_ID = "test-merchant"


async def _seed_broker_user(db_session: AsyncSession) -> PlatformUser:
    broker = Broker(name="Bulk Validation Brokers", contact_email=f"{uuid.uuid4()}@example.com")
    db_session.add(broker)
    await db_session.flush()
    user = PlatformUser(
        email=f"{uuid.uuid4()}@example.com", role=Role.BROKER_ADMIN.value, broker_id=broker.id
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def test_empty_installment_list_is_rejected(db_session: AsyncSession) -> None:
    user = await _seed_broker_user(db_session)
    with pytest.raises(UnprocessableError, match="must not be empty"):
        await initiate_bulk_payment(
            db_session,
            actor=user,
            installment_ids=[],
            broker_id=user.broker_id,
            squad_client=FakeSquadClient(),
            merchant_id=_MERCHANT_ID,
            max_items=500,
        )


async def test_batch_exceeding_cap_is_rejected_before_any_db_or_squad_work(
    db_session: AsyncSession,
) -> None:
    user = await _seed_broker_user(db_session)
    fake = FakeSquadClient()
    installment_ids = [uuid.uuid4() for _ in range(4)]
    with pytest.raises(UnprocessableError, match="exceeds the cap"):
        await initiate_bulk_payment(
            db_session,
            actor=user,
            installment_ids=installment_ids,
            broker_id=user.broker_id,
            squad_client=fake,
            merchant_id=_MERCHANT_ID,
            max_items=3,
        )
    assert fake.created_accounts == {}


async def test_duplicate_installment_ids_are_rejected(db_session: AsyncSession) -> None:
    user = await _seed_broker_user(db_session)
    dup_id = uuid.uuid4()
    fake = FakeSquadClient()
    with pytest.raises(UnprocessableError, match="duplicates"):
        await initiate_bulk_payment(
            db_session,
            actor=user,
            installment_ids=[dup_id, dup_id],
            broker_id=user.broker_id,
            squad_client=fake,
            merchant_id=_MERCHANT_ID,
            max_items=500,
        )
    assert fake.created_accounts == {}


async def test_nonexistent_installment_id_raises_not_found_before_any_squad_call(
    db_session: AsyncSession,
) -> None:
    user = await _seed_broker_user(db_session)
    fake = FakeSquadClient()
    with pytest.raises(NotFoundError):
        await initiate_bulk_payment(
            db_session,
            actor=user,
            installment_ids=[uuid.uuid4()],
            broker_id=user.broker_id,
            squad_client=fake,
            merchant_id=_MERCHANT_ID,
            max_items=500,
        )
    assert fake.created_accounts == {}
