import hashlib
import json
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.models.idempotency_key import IdempotencyKey


def hash_request_body(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


async def claim_idempotency_key(
    db: AsyncSession,
    *,
    platform_user_id: uuid.UUID,
    endpoint: str,
    idempotency_key: str,
    request_body: dict[str, Any],
) -> tuple[IdempotencyKey, bool]:
    """Claims (user, endpoint, key) via INSERT ... ON CONFLICT DO NOTHING, so
    two concurrent first-calls with the same key race into the same row
    instead of each separately calling Squad. Returns (row, is_new) -- when
    is_new is False, the caller must check whether response_status is still
    NULL (another call is in flight) before treating it as a cached replay.
    """
    request_hash = hash_request_body(request_body)
    stmt = (
        pg_insert(IdempotencyKey)
        .values(
            platform_user_id=platform_user_id,
            endpoint=endpoint,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        .on_conflict_do_nothing(constraint="ux_idempotency_keys_user_endpoint_key")
        .returning(IdempotencyKey)
    )
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if row is not None:
        await db.flush()
        return row, True

    existing = await db.scalar(
        select(IdempotencyKey).where(
            IdempotencyKey.platform_user_id == platform_user_id,
            IdempotencyKey.endpoint == endpoint,
            IdempotencyKey.idempotency_key == idempotency_key,
        )
    )
    if existing is None:
        raise ConflictError("idempotency key claim conflicted but no existing row was found")
    if existing.request_hash != request_hash:
        raise ConflictError("idempotency key reused with a different request body")
    return existing, False


async def complete_idempotency_key(
    db: AsyncSession,
    key_row: IdempotencyKey,
    *,
    response_status: int,
    response_body: dict[str, Any],
    resource_id: uuid.UUID | None = None,
) -> None:
    key_row.response_status = response_status
    key_row.response_body = response_body
    key_row.resource_id = resource_id
    await db.flush()


async def with_idempotency(
    db: AsyncSession,
    *,
    platform_user_id: uuid.UUID,
    endpoint: str,
    idempotency_key: str,
    request_body: dict[str, Any],
    handler: Callable[[uuid.UUID], Awaitable[tuple[int, dict[str, Any], uuid.UUID | None]]],
) -> tuple[int, dict[str, Any]]:
    """Wraps a payment-initiating handler so replays return the original
    response verbatim instead of re-triggering it (CLAUDE.md). A same-key
    different-payload reuse, or a key whose first call is still in flight,
    both raise ConflictError -- never silently proceeds with a duplicate
    charge. The claimed key's id is passed into the handler so the created
    resource (e.g. Payment.idempotency_key_id) can point back at it.
    """
    key_row, is_new = await claim_idempotency_key(
        db,
        platform_user_id=platform_user_id,
        endpoint=endpoint,
        idempotency_key=idempotency_key,
        request_body=request_body,
    )
    if not is_new:
        if key_row.response_status is None:
            raise ConflictError("a request with this idempotency key is already in flight")
        return key_row.response_status, key_row.response_body or {}

    status_code, response_body, resource_id = await handler(key_row.id)
    await complete_idempotency_key(
        db,
        key_row,
        response_status=status_code,
        response_body=response_body,
        resource_id=resource_id,
    )
    return status_code, response_body
