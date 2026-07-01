import uuid
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user, get_tenant_id, require_permission
from app.models.platform_user import PlatformUser
from app.models.policy import Policy
from app.models.premium_installment import PremiumInstallment
from app.rbac.permissions import Permission, Role
from app.schemas.policy import InstallmentOut, PolicyCreateRequest, PolicyOut
from app.services import policy_service

router = APIRouter(prefix="/policies", tags=["policies"])


def _check_policy_access(policy: Policy, actor: PlatformUser, tenant_id: uuid.UUID | None) -> None:
    if tenant_id is not None and policy.insurance_company_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    role = Role(actor.role)
    if role in (Role.BROKER_ADMIN, Role.BROKER_STAFF) and policy.broker_id != actor.broker_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("", response_model=PolicyOut, status_code=status.HTTP_201_CREATED)
async def create_policy(
    payload: PolicyCreateRequest,
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.CREATE_POLICY))],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PolicyOut:
    # CREATE_POLICY is granted only to broker roles, for which get_tenant_id
    # always resolves a concrete tenant (or raises 409).
    insurance_company_id = cast(uuid.UUID, tenant_id)
    policy = await policy_service.create_policy(
        db,
        actor=actor,
        insurance_company_id=insurance_company_id,
        policyholder_id=payload.policyholder_id,
        premium_amount_kobo=payload.premium_amount_kobo,
        premium_frequency=payload.premium_frequency,
        start_date=payload.start_date,
        policy_type=payload.policy_type,
    )
    return PolicyOut.model_validate(policy)


@router.get("/{policy_id}", response_model=PolicyOut)
async def get_policy(
    policy_id: uuid.UUID,
    actor: Annotated[PlatformUser, Depends(get_current_user)],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PolicyOut:
    policy = await db.get(Policy, policy_id)
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="policy not found")
    _check_policy_access(policy, actor, tenant_id)
    return PolicyOut.model_validate(policy)


@router.get("", response_model=list[PolicyOut])
async def list_policies(
    user_id: uuid.UUID,
    actor: Annotated[PlatformUser, Depends(get_current_user)],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PolicyOut]:
    stmt = select(Policy).where(Policy.policyholder_id == user_id)
    if tenant_id is not None:
        stmt = stmt.where(Policy.insurance_company_id == tenant_id)
    role = Role(actor.role)
    if role in (Role.BROKER_ADMIN, Role.BROKER_STAFF):
        stmt = stmt.where(Policy.broker_id == actor.broker_id)
    result = await db.scalars(stmt)
    return [PolicyOut.model_validate(p) for p in result.all()]


@router.get("/{policy_id}/installments", response_model=list[InstallmentOut])
async def list_policy_installments(
    policy_id: uuid.UUID,
    actor: Annotated[PlatformUser, Depends(get_current_user)],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[InstallmentOut]:
    policy = await db.get(Policy, policy_id)
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="policy not found")
    _check_policy_access(policy, actor, tenant_id)

    result = await db.scalars(
        select(PremiumInstallment)
        .where(PremiumInstallment.policy_id == policy_id)
        .order_by(PremiumInstallment.due_date)
    )
    return [InstallmentOut.model_validate(i) for i in result.all()]
