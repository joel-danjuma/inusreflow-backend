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
from app.models.policyholder import Policyholder
from app.rbac.permissions import Permission, Role
from app.schemas.policy import PolicyholderCreateRequest, PolicyholderOut
from app.services import policy_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=PolicyholderOut, status_code=status.HTTP_201_CREATED)
async def create_policyholder(
    payload: PolicyholderCreateRequest,
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.CREATE_POLICYHOLDER))],
    company_id: Annotated[uuid.UUID, Depends(get_own_insurer_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PolicyholderOut:
    # CREATE_POLICYHOLDER is granted only to INSURANCE_COMPANY_ADMIN, for
    # which get_own_insurer_id always resolves a concrete tenant. The
    # insurer names which of their assigned brokers this policyholder
    # belongs to explicitly -- validated here before it reaches the service.
    await assert_broker_assigned_to_insurer(
        db, insurer_id=company_id, broker_id=payload.broker_id
    )
    policyholder = await policy_service.create_policyholder(
        db,
        actor=actor,
        insurance_company_id=company_id,
        broker_id=payload.broker_id,
        full_name=payload.full_name,
        email=payload.email,
        phone_number=payload.phone_number,
        identification_number=payload.identification_number,
    )
    return PolicyholderOut.model_validate(policyholder)


@router.get("/{policyholder_id}", response_model=PolicyholderOut)
async def get_policyholder(
    policyholder_id: uuid.UUID,
    actor: Annotated[PlatformUser, Depends(get_current_user)],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PolicyholderOut:
    policyholder = await db.get(Policyholder, policyholder_id)
    if policyholder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="policyholder not found")

    if tenant_id is not None and policyholder.insurance_company_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    role = Role(actor.role)
    if role in (Role.BROKER_ADMIN, Role.BROKER_STAFF) and policyholder.broker_id != actor.broker_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return PolicyholderOut.model_validate(policyholder)


@router.get("", response_model=list[PolicyholderOut])
async def list_policyholders(
    actor: Annotated[PlatformUser, Depends(get_current_user)],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    broker_id: Annotated[uuid.UUID | None, Query()] = None,
) -> list[PolicyholderOut]:
    """broker_id narrows to one broker's policyholders; omitted returns
    every policyholder the caller can see -- their whole tenant for an
    Insurance Company Admin, their own broker's for broker roles (who may
    only ever narrow to their own broker_id, never anyone else's).
    """
    role = Role(actor.role)
    if role in (Role.BROKER_ADMIN, Role.BROKER_STAFF):
        if broker_id is not None and actor.broker_id != broker_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        broker_id = actor.broker_id

    stmt = select(Policyholder)
    if broker_id is not None:
        stmt = stmt.where(Policyholder.broker_id == broker_id)
    if tenant_id is not None:
        stmt = stmt.where(Policyholder.insurance_company_id == tenant_id)
    result = await db.scalars(stmt)
    return [PolicyholderOut.model_validate(p) for p in result.all()]
