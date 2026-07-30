import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    get_broker_insurer_filter,
    get_current_user,
    get_tenant_id,
    require_permission,
)
from app.models.enums import InstallmentStatus
from app.models.platform_user import PlatformUser
from app.models.policy import Policy
from app.models.premium_installment import PremiumInstallment
from app.rbac.permissions import Permission, Role
from app.schemas.policy import InstallmentOut
from app.services import installment_service

router = APIRouter(prefix="/installments", tags=["installments"])


def _check_installment_access(
    policy: Policy, actor: PlatformUser, tenant_id: uuid.UUID | None
) -> None:
    if tenant_id is not None and policy.insurance_company_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    role = Role(actor.role)
    if role in (Role.BROKER_ADMIN, Role.BROKER_STAFF) and policy.broker_id != actor.broker_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


class InstallmentReferenceNumberSetRequest(BaseModel):
    reference_number: str | None = Field(default=None, max_length=255)


@router.get("", response_model=list[InstallmentOut])
async def list_installments(
    actor: Annotated[PlatformUser, Depends(get_current_user)],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    insurer_id: Annotated[uuid.UUID | None, Depends(get_broker_insurer_filter)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Annotated[InstallmentStatus | None, Query(alias="status")] = None,
    policy_type_filter: Annotated[str | None, Query(alias="policy_type")] = None,
) -> list[InstallmentOut]:
    """Implicitly scoped to the caller's own visibility — Insureflow Admin
    sees every installment, an Insurance Company Admin sees every installment
    under their tenant, and broker roles see their own broker's across every
    insurer they work with by default, or one via insurer_id narrowing
    (get_broker_insurer_filter is a no-op for non-broker roles).
    """
    stmt = select(PremiumInstallment, Policy.policy_type).join(
        Policy, PremiumInstallment.policy_id == Policy.id
    )
    if tenant_id is not None:
        stmt = stmt.where(Policy.insurance_company_id == tenant_id)
    role = Role(actor.role)
    if role in (Role.BROKER_ADMIN, Role.BROKER_STAFF):
        stmt = stmt.where(Policy.broker_id == actor.broker_id)
        if insurer_id is not None:
            stmt = stmt.where(Policy.insurance_company_id == insurer_id)
    if status_filter is not None:
        stmt = stmt.where(PremiumInstallment.status == status_filter.value)
    if policy_type_filter is not None:
        stmt = stmt.where(func.lower(Policy.policy_type) == policy_type_filter.lower())
    stmt = stmt.order_by(PremiumInstallment.due_date)

    result = await db.execute(stmt)
    return [
        InstallmentOut(
            id=i.id,
            policy_id=i.policy_id,
            due_date=i.due_date,
            amount_kobo=i.amount_kobo,
            status=i.status,
            payment_id=i.payment_id,
            payment_batch_item_id=i.payment_batch_item_id,
            reference_number=i.reference_number,
            policy_type=policy_type,
            created_at=i.created_at,
        )
        for i, policy_type in result.all()
    ]


@router.patch("/{installment_id}/reference-number", response_model=InstallmentOut)
async def set_installment_reference_number(
    installment_id: uuid.UUID,
    payload: InstallmentReferenceNumberSetRequest,
    actor: Annotated[
        PlatformUser, Depends(require_permission(Permission.MANAGE_INSTALLMENT_REFERENCE))
    ],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InstallmentOut:
    installment = await db.get(PremiumInstallment, installment_id)
    if installment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="installment not found")
    policy = await db.get(Policy, installment.policy_id)
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="installment not found")
    _check_installment_access(policy, actor, tenant_id)

    installment = await installment_service.set_reference_number(
        db, installment=installment, reference_number=payload.reference_number, actor=actor
    )
    return InstallmentOut(
        id=installment.id,
        policy_id=installment.policy_id,
        due_date=installment.due_date,
        amount_kobo=installment.amount_kobo,
        status=installment.status,
        payment_id=installment.payment_id,
        payment_batch_item_id=installment.payment_batch_item_id,
        reference_number=installment.reference_number,
        policy_type=policy.policy_type,
        created_at=installment.created_at,
    )
