import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user, require_permission
from app.models.broker import Broker
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Permission, Role
from app.schemas.onboarding import (
    ApprovalResult,
    BrokerOnboardRequest,
    BrokerOut,
    CreateBrokerStaffRequest,
)
from app.services import onboarding_service

router = APIRouter(prefix="/brokers", tags=["brokers"])


@router.post("", response_model=BrokerOut, status_code=status.HTTP_201_CREATED)
async def onboard_broker(
    payload: BrokerOnboardRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BrokerOut:
    broker = await onboarding_service.onboard_broker(
        db, name=payload.name, contact_email=payload.contact_email
    )
    return BrokerOut.model_validate(broker)


@router.get("/{broker_id}", response_model=BrokerOut)
async def get_broker(
    broker_id: uuid.UUID,
    user: Annotated[PlatformUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BrokerOut:
    if Role(user.role) is not Role.INSUREFLOW_ADMIN and user.broker_id != broker_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    broker = await db.get(Broker, broker_id)
    if broker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="broker not found")
    return BrokerOut.model_validate(broker)


@router.post(
    "/{broker_id}/staff", response_model=ApprovalResult, status_code=status.HTTP_201_CREATED
)
async def create_broker_staff(
    broker_id: uuid.UUID,
    payload: CreateBrokerStaffRequest,
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.MANAGE_BROKER_STAFF))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApprovalResult:
    if actor.broker_id != broker_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    _, raw_token = await onboarding_service.create_broker_staff_user(
        db, broker_id=broker_id, email=payload.email, actor=actor
    )
    return ApprovalResult(activation_token=raw_token)
