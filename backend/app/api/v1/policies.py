import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    assert_broker_assigned_to_insurer,
    get_current_user,
    get_own_insurer_id,
    get_tenant_id,
    require_permission,
)
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
    company_id: Annotated[uuid.UUID, Depends(get_own_insurer_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PolicyOut:
    # CREATE_POLICY is granted only to INSURANCE_COMPANY_ADMIN, for which
    # get_own_insurer_id always resolves a concrete tenant. The insurer names
    # which of their assigned brokers this policy belongs to explicitly --
    # validated here before it ever reaches the service layer.
    await assert_broker_assigned_to_insurer(
        db, insurer_id=company_id, broker_id=payload.broker_id
    )
    policy = await policy_service.create_policy(
        db,
        actor=actor,
        insurance_company_id=company_id,
        broker_id=payload.broker_id,
        reference_number=payload.reference_number,
        policyholder_id=payload.policyholder_id,
        premium_amount_kobo=payload.premium_amount_kobo,
        premium_frequency=payload.premium_frequency,
        start_date=payload.start_date,
        policy_type=payload.policy_type,
        policy_name=payload.policy_name,
        duration_months=payload.duration_months,
        coverage_amount_kobo=payload.coverage_amount_kobo,
        coverage_items=payload.coverage_items,
        beneficiaries=payload.beneficiaries,
        broker_notes=payload.broker_notes,
        internal_tags=payload.internal_tags,
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
    actor: Annotated[PlatformUser, Depends(get_current_user)],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[uuid.UUID | None, Query()] = None,
) -> list[PolicyOut]:
    """user_id narrows to one policyholder's policies; omitted returns every
    policy the caller can see -- their whole tenant for an Insurance Company
    Admin (optionally further narrowed by Change 1's broker_id selector on
    the dashboard, not here), their own broker's book for broker roles.
    """
    stmt = select(Policy)
    if user_id is not None:
        stmt = stmt.where(Policy.policyholder_id == user_id)
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
            policy_type=policy.policy_type,
            created_at=i.created_at,
        )
        for i in result.all()
    ]
