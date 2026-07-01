import uuid
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import get_squad_client, get_tenant_id, require_permission
from app.core.rate_limit import enforce_payment_rate_limit
from app.integrations.squad.client import SquadClient
from app.models.payment import Payment
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Permission, Role
from app.schemas.payment import PaymentCreateRequest, PaymentOut
from app.services import idempotency_service, payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


def _check_payment_access(
    payment: Payment, actor: PlatformUser, tenant_id: uuid.UUID | None
) -> None:
    if tenant_id is not None and payment.insurance_company_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    role = Role(actor.role)
    if role in (Role.BROKER_ADMIN, Role.BROKER_STAFF) and payment.broker_id != actor.broker_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post(
    "",
    response_model=PaymentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_payment_rate_limit)],
)
async def create_payment(
    payload: PaymentCreateRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.CREATE_PAYMENT))],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    squad_client: Annotated[SquadClient, Depends(get_squad_client)],
) -> PaymentOut:
    # CREATE_PAYMENT is granted only to broker roles, for which get_tenant_id
    # always resolves a concrete tenant (or raises 409) and broker_id is set.
    insurance_company_id = cast(uuid.UUID, tenant_id)
    broker_id = cast(uuid.UUID, actor.broker_id)
    settings = get_settings()

    async def handler(key_id: uuid.UUID) -> tuple[int, dict[str, Any], uuid.UUID | None]:
        payment = await payment_service.initiate_payment(
            db,
            actor=actor,
            installment_id=payload.installment_id,
            broker_id=broker_id,
            insurance_company_id=insurance_company_id,
            squad_client=squad_client,
            merchant_id=settings.squad_merchant_id,
            duration_seconds=settings.squad_dynamic_va_duration_seconds,
            idempotency_key_id=key_id,
        )
        body = PaymentOut.model_validate(payment).model_dump(mode="json")
        return status.HTTP_201_CREATED, body, payment.id

    _, body = await idempotency_service.with_idempotency(
        db,
        platform_user_id=actor.id,
        endpoint="POST /payments",
        idempotency_key=idempotency_key,
        request_body=payload.model_dump(mode="json"),
        handler=handler,
    )
    return PaymentOut.model_validate(body)


@router.get("/{payment_id}", response_model=PaymentOut)
async def get_payment(
    payment_id: uuid.UUID,
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.VIEW_PAYMENTS))],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaymentOut:
    payment = await db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="payment not found")
    _check_payment_access(payment, actor, tenant_id)
    return PaymentOut.model_validate(payment)
