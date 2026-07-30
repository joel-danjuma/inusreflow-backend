import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import get_squad_client, require_permission
from app.integrations.squad.client import SquadClient
from app.models.broker import Broker
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Permission, Role
from app.schemas.onboarding import BrokerKybUpdateRequest
from app.services import onboarding_service

router = APIRouter(prefix="/virtual-accounts", tags=["virtual-accounts"])


class VirtualAccountOut(BaseModel):
    broker_id: uuid.UUID
    broker_name: str
    squad_va_number: str | None
    squad_va_bank: str | None
    squad_customer_identifier: str | None
    created_at: datetime

    model_config = {"from_attributes": False}


def _broker_to_va_out(broker: Broker) -> VirtualAccountOut:
    return VirtualAccountOut(
        broker_id=broker.id,
        broker_name=broker.name,
        squad_va_number=broker.squad_va_number,
        squad_va_bank=broker.squad_va_bank,
        squad_customer_identifier=broker.squad_customer_identifier,
        created_at=broker.created_at,
    )


@router.get("", response_model=list[VirtualAccountOut])
async def list_virtual_accounts(
    actor: Annotated[
        PlatformUser, Depends(require_permission(Permission.VIEW_ALL_VIRTUAL_ACCOUNTS))
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[VirtualAccountOut]:
    brokers = (await db.scalars(select(Broker))).all()
    return [_broker_to_va_out(b) for b in brokers]


@router.post("/{broker_id}", response_model=VirtualAccountOut, status_code=status.HTTP_200_OK)
async def create_or_recreate_virtual_account(
    broker_id: uuid.UUID,
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.MANAGE_VIRTUAL_ACCOUNTS))],
    db: Annotated[AsyncSession, Depends(get_db)],
    squad_client: Annotated[SquadClient, Depends(get_squad_client)],
) -> VirtualAccountOut:
    settings = get_settings()
    broker = await onboarding_service.create_broker_virtual_account(
        db,
        broker_id=broker_id,
        squad_client=squad_client,
        beneficiary_account=settings.squad_beneficiary_account,
        actor=actor,
    )
    return _broker_to_va_out(broker)


@router.get("/me", response_model=VirtualAccountOut)
async def get_own_virtual_account(
    actor: Annotated[
        PlatformUser, Depends(require_permission(Permission.VIEW_OWN_VIRTUAL_ACCOUNT))
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VirtualAccountOut:
    if Role(actor.role) not in (Role.BROKER_ADMIN, Role.BROKER_STAFF):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if actor.broker_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    broker = await db.get(Broker, actor.broker_id)
    if broker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="broker not found")
    return _broker_to_va_out(broker)


@router.patch("/me", response_model=VirtualAccountOut)
async def update_own_broker_kyb(
    payload: BrokerKybUpdateRequest,
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.MANAGE_OWN_BROKER))],
    db: Annotated[AsyncSession, Depends(get_db)],
    squad_client: Annotated[SquadClient, Depends(get_squad_client)],
) -> VirtualAccountOut:
    """Broker self-service: onboarding no longer collects bvn/phone_number
    upfront, so this is the only path to provision (or fix) a virtual
    account after the fact -- sets the KYB fields and immediately attempts
    provisioning with them, same as the admin recreate action.
    """
    if actor.broker_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    settings = get_settings()
    broker = await onboarding_service.create_broker_virtual_account(
        db,
        broker_id=actor.broker_id,
        squad_client=squad_client,
        beneficiary_account=settings.squad_beneficiary_account,
        actor=actor,
        bvn=payload.bvn,
        phone_number=payload.phone_number,
    )
    return _broker_to_va_out(broker)
