import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import get_squad_client, get_tenant_id, require_permission
from app.core.exceptions import NotFoundError
from app.integrations.squad.client import SquadClient
from app.models.insurance_company import InsuranceCompany
from app.models.platform_user import PlatformUser
from app.models.settlement_payout import SettlementPayout
from app.rbac.permissions import Permission
from app.schemas.settlement import SettlementPayoutOut
from app.services import settlement_service

router = APIRouter(prefix="/settlements", tags=["settlements"])


@router.get("", response_model=list[SettlementPayoutOut])
async def list_settlements(
    _: Annotated[PlatformUser, Depends(require_permission(Permission.VIEW_SETTLEMENTS))],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
) -> list[SettlementPayoutOut]:
    """VIEW_SETTLEMENTS is only granted to Insureflow Admin (cross-tenant,
    tenant_id is None) and Insurance Company Admin (own tenant only).
    """
    stmt = select(SettlementPayout)
    if tenant_id is not None:
        stmt = stmt.where(SettlementPayout.insurance_company_id == tenant_id)
    if status_filter is not None:
        stmt = stmt.where(SettlementPayout.status == status_filter)
    stmt = stmt.order_by(SettlementPayout.created_at.desc())

    result = await db.scalars(stmt)
    return [SettlementPayoutOut.model_validate(s) for s in result.all()]


@router.get("/{payout_id}", response_model=SettlementPayoutOut)
async def get_settlement(
    payout_id: uuid.UUID,
    _: Annotated[PlatformUser, Depends(require_permission(Permission.VIEW_SETTLEMENTS))],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SettlementPayoutOut:
    payout = await db.get(SettlementPayout, payout_id)
    if payout is None:
        raise NotFoundError(f"settlement payout {payout_id} not found")
    if tenant_id is not None and payout.insurance_company_id != tenant_id:
        raise NotFoundError(f"settlement payout {payout_id} not found")
    return SettlementPayoutOut.model_validate(payout)


@router.post("/{payout_id}/retry", response_model=SettlementPayoutOut)
async def retry_settlement_payout(
    payout_id: uuid.UUID,
    _: Annotated[PlatformUser, Depends(require_permission(Permission.RETRY_SETTLEMENT_PAYOUT))],
    db: Annotated[AsyncSession, Depends(get_db)],
    squad_client: Annotated[SquadClient, Depends(get_squad_client)],
) -> SettlementPayoutOut:
    payout = await db.get(SettlementPayout, payout_id)
    if payout is None:
        raise NotFoundError(f"settlement payout {payout_id} not found")

    insurance_company = await db.get(InsuranceCompany, payout.insurance_company_id)
    if insurance_company is None:
        raise NotFoundError(f"insurance company {payout.insurance_company_id} not found")

    settings = get_settings()
    new_payout = await settlement_service.retry_failed_settlement(
        db,
        payout,
        insurance_company=insurance_company,
        squad_client=squad_client,
        merchant_id=settings.squad_merchant_id,
    )
    return SettlementPayoutOut.model_validate(new_payout)
