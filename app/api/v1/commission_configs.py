import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user, get_tenant_id, require_permission
from app.models.broker_insurer_assignment import BrokerInsurerAssignment
from app.models.commission_config import CommissionConfig
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Permission, Role
from app.schemas.commission import CommissionConfigCreateRequest, CommissionConfigOut
from app.services import commission_service

router = APIRouter(prefix="/commission-configs", tags=["commission-configs"])


@router.post("", response_model=CommissionConfigOut, status_code=status.HTTP_201_CREATED)
async def create_commission_config(
    payload: CommissionConfigCreateRequest,
    actor: Annotated[PlatformUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CommissionConfigOut:
    """A single endpoint handles every scope (PRD §10) since the write
    permission depends on the request body's `scope`, not just the route:
    global/insurance_company rates are an Insureflow Admin call, broker
    rates are set by the broker's own Insurance Company Admin.
    """
    role = Role(actor.role)
    if payload.scope in ("global", "insurance_company"):
        if role is not Role.INSUREFLOW_ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    else:
        if role is not Role.INSURANCE_COMPANY_ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        assignment = await db.scalar(
            select(BrokerInsurerAssignment).where(
                BrokerInsurerAssignment.broker_id == payload.broker_id,
                BrokerInsurerAssignment.insurance_company_id == actor.insurance_company_id,
                BrokerInsurerAssignment.is_active.is_(True),
            )
        )
        if assignment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Broker not found")

    config = await commission_service.set_commission_config(
        db,
        actor=actor,
        scope=payload.scope,
        gtbank_rate_bps=payload.gtbank_rate_bps,
        insureflow_rate_bps=payload.insureflow_rate_bps,
        broker_rate_bps=payload.broker_rate_bps,
        insurance_company_id=payload.insurance_company_id,
        broker_id=payload.broker_id,
    )
    return CommissionConfigOut.model_validate(config)


@router.get("", response_model=list[CommissionConfigOut])
async def list_commission_configs(
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.VIEW_COMMISSION_CONFIGS))],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CommissionConfigOut]:
    role = Role(actor.role)
    stmt = select(CommissionConfig)

    if role is Role.INSURANCE_COMPANY_ADMIN:
        own_broker_ids = select(BrokerInsurerAssignment.broker_id).where(
            BrokerInsurerAssignment.insurance_company_id == tenant_id,
            BrokerInsurerAssignment.is_active.is_(True),
        )
        stmt = stmt.where(
            or_(
                CommissionConfig.scope == "global",
                and_(
                    CommissionConfig.scope == "insurance_company",
                    CommissionConfig.insurance_company_id == tenant_id,
                ),
                and_(
                    CommissionConfig.scope == "broker",
                    CommissionConfig.broker_id.in_(own_broker_ids),
                ),
            )
        )
    elif role in (Role.BROKER_ADMIN, Role.BROKER_STAFF):
        stmt = stmt.where(
            or_(
                CommissionConfig.scope == "global",
                and_(
                    CommissionConfig.scope == "broker",
                    CommissionConfig.broker_id == actor.broker_id,
                ),
            )
        )

    stmt = stmt.order_by(CommissionConfig.effective_from.desc())
    result = await db.scalars(stmt)
    return [CommissionConfigOut.model_validate(c) for c in result.all()]
