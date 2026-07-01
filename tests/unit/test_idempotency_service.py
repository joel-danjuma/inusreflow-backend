import uuid
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.models.broker import Broker
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Role
from app.services.idempotency_service import claim_idempotency_key, with_idempotency

_ENDPOINT = "POST /payments"


async def _seed_user(db_session: AsyncSession) -> PlatformUser:
    broker = Broker(name="Idempotency Test Brokers", contact_email=f"{uuid.uuid4()}@example.com")
    db_session.add(broker)
    await db_session.flush()
    user = PlatformUser(
        email=f"{uuid.uuid4()}@example.com", role=Role.BROKER_ADMIN.value, broker_id=broker.id
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def test_claim_is_new_on_first_call(db_session: AsyncSession) -> None:
    user = await _seed_user(db_session)
    key_row, is_new = await claim_idempotency_key(
        db_session,
        platform_user_id=user.id,
        endpoint=_ENDPOINT,
        idempotency_key="key-1",
        request_body={"installment_id": "abc"},
    )
    assert is_new is True
    assert key_row.response_status is None


async def test_claim_same_payload_returns_existing_row(db_session: AsyncSession) -> None:
    user = await _seed_user(db_session)
    body = {"installment_id": "abc"}
    first, _ = await claim_idempotency_key(
        db_session,
        platform_user_id=user.id,
        endpoint=_ENDPOINT,
        idempotency_key="key-2",
        request_body=body,
    )
    second, is_new = await claim_idempotency_key(
        db_session,
        platform_user_id=user.id,
        endpoint=_ENDPOINT,
        idempotency_key="key-2",
        request_body=body,
    )
    assert is_new is False
    assert second.id == first.id


async def test_claim_different_payload_same_key_raises_conflict(db_session: AsyncSession) -> None:
    user = await _seed_user(db_session)
    await claim_idempotency_key(
        db_session,
        platform_user_id=user.id,
        endpoint=_ENDPOINT,
        idempotency_key="key-3",
        request_body={"installment_id": "abc"},
    )
    with pytest.raises(ConflictError, match="different request body"):
        await claim_idempotency_key(
            db_session,
            platform_user_id=user.id,
            endpoint=_ENDPOINT,
            idempotency_key="key-3",
            request_body={"installment_id": "xyz"},
        )


async def test_with_idempotency_replay_returns_cached_response_without_rerunning_handler(
    db_session: AsyncSession,
) -> None:
    user = await _seed_user(db_session)
    calls = 0

    async def handler(key_id: uuid.UUID) -> tuple[int, dict[str, Any], uuid.UUID | None]:
        nonlocal calls
        calls += 1
        return 201, {"ok": True}, uuid.uuid4()

    body = {"installment_id": "abc"}
    result1 = await with_idempotency(
        db_session,
        platform_user_id=user.id,
        endpoint=_ENDPOINT,
        idempotency_key="key-4",
        request_body=body,
        handler=handler,
    )
    result2 = await with_idempotency(
        db_session,
        platform_user_id=user.id,
        endpoint=_ENDPOINT,
        idempotency_key="key-4",
        request_body=body,
        handler=handler,
    )
    assert calls == 1
    assert result1 == result2 == (201, {"ok": True})


async def test_with_idempotency_in_flight_key_raises_conflict(db_session: AsyncSession) -> None:
    user = await _seed_user(db_session)
    await claim_idempotency_key(
        db_session,
        platform_user_id=user.id,
        endpoint=_ENDPOINT,
        idempotency_key="key-5",
        request_body={"installment_id": "abc"},
    )

    async def handler(key_id: uuid.UUID) -> tuple[int, dict[str, Any], uuid.UUID | None]:
        return 201, {}, None

    with pytest.raises(ConflictError, match="already in flight"):
        await with_idempotency(
            db_session,
            platform_user_id=user.id,
            endpoint=_ENDPOINT,
            idempotency_key="key-5",
            request_body={"installment_id": "abc"},
            handler=handler,
        )
