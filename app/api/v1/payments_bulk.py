import uuid
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import get_squad_client, get_tenant_id, require_permission
from app.core.rate_limit import enforce_payment_rate_limit
from app.integrations.squad.client import SquadClient
from app.models.payment_batch import PaymentBatch
from app.models.payment_batch_item import PaymentBatchItem
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Permission, Role
from app.schemas.payment_batch import (
    PaymentBatchCreateRequest,
    PaymentBatchItemOut,
    PaymentBatchOut,
)
from app.services import bulk_payment_service, idempotency_service

router = APIRouter(prefix="/payments/bulk", tags=["payments"])


def _check_batch_access(
    batch: PaymentBatch, actor: PlatformUser, tenant_id: uuid.UUID | None
) -> None:
    if tenant_id is not None and batch.insurance_company_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    role = Role(actor.role)
    if role in (Role.BROKER_ADMIN, Role.BROKER_STAFF) and batch.broker_id != actor.broker_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def _build_batch_out(db: AsyncSession, batch: PaymentBatch) -> PaymentBatchOut:
    """No ORM relationships in this codebase (CLAUDE.md) -- items are
    fetched and assembled manually rather than relying on attribute
    traversal.
    """
    items = (
        await db.scalars(
            select(PaymentBatchItem).where(PaymentBatchItem.payment_batch_id == batch.id)
        )
    ).all()
    return PaymentBatchOut(
        id=batch.id,
        broker_id=batch.broker_id,
        insurance_company_id=batch.insurance_company_id,
        total_amount_kobo=batch.total_amount_kobo,
        item_count=batch.item_count,
        status=batch.status,
        squad_transaction_ref=batch.squad_transaction_ref,
        squad_virtual_account_number=batch.squad_virtual_account_number,
        squad_virtual_account_bank=batch.squad_virtual_account_bank,
        va_expires_at=batch.va_expires_at,
        failure_reason=batch.failure_reason,
        created_at=batch.created_at,
        items=[PaymentBatchItemOut.model_validate(item) for item in items],
    )


@router.post(
    "",
    response_model=PaymentBatchOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_payment_rate_limit)],
)
async def create_bulk_payment(
    payload: PaymentBatchCreateRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.CREATE_PAYMENT))],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    squad_client: Annotated[SquadClient, Depends(get_squad_client)],
) -> PaymentBatchOut:
    # CREATE_PAYMENT is granted only to broker roles, for which get_tenant_id
    # always resolves a concrete tenant (or raises 409) and broker_id is set.
    insurance_company_id = cast(uuid.UUID, tenant_id)
    broker_id = cast(uuid.UUID, actor.broker_id)
    settings = get_settings()

    async def handler(key_id: uuid.UUID) -> tuple[int, dict[str, Any], uuid.UUID | None]:
        batch = await bulk_payment_service.initiate_bulk_payment(
            db,
            actor=actor,
            installment_ids=payload.installment_ids,
            broker_id=broker_id,
            insurance_company_id=insurance_company_id,
            squad_client=squad_client,
            merchant_id=settings.squad_merchant_id,
            duration_seconds=settings.squad_dynamic_va_duration_seconds,
            max_items=settings.max_bulk_payment_items,
            idempotency_key_id=key_id,
        )
        body = (await _build_batch_out(db, batch)).model_dump(mode="json")
        return status.HTTP_201_CREATED, body, batch.id

    _, body = await idempotency_service.with_idempotency(
        db,
        platform_user_id=actor.id,
        endpoint="POST /payments/bulk",
        idempotency_key=idempotency_key,
        request_body=payload.model_dump(mode="json"),
        handler=handler,
    )
    return PaymentBatchOut.model_validate(body)


@router.get("/{batch_id}", response_model=PaymentBatchOut)
async def get_bulk_payment(
    batch_id: uuid.UUID,
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.VIEW_PAYMENTS))],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaymentBatchOut:
    batch = await db.get(PaymentBatch, batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="payment batch not found")
    _check_batch_access(batch, actor, tenant_id)
    return await _build_batch_out(db, batch)
