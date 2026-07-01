import uuid
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user, get_tenant_id, require_permission
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
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PolicyholderOut:
    # CREATE_POLICYHOLDER is granted only to broker roles, for which
    # get_tenant_id always resolves a concrete tenant (or raises 409).
    insurance_company_id = cast(uuid.UUID, tenant_id)
    policyholder = await policy_service.create_policyholder(
        db,
        actor=actor,
        insurance_company_id=insurance_company_id,
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
    broker_id: uuid.UUID,
    actor: Annotated[PlatformUser, Depends(get_current_user)],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PolicyholderOut]:
    role = Role(actor.role)
    if role in (Role.BROKER_ADMIN, Role.BROKER_STAFF) and actor.broker_id != broker_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    stmt = select(Policyholder).where(Policyholder.broker_id == broker_id)
    if tenant_id is not None:
        stmt = stmt.where(Policyholder.insurance_company_id == tenant_id)
    result = await db.scalars(stmt)
    return [PolicyholderOut.model_validate(p) for p in result.all()]
