import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import get_squad_client, require_permission
from app.core.exceptions import NotFoundError
from app.integrations.squad.client import SquadClient
from app.models.insurance_company import InsuranceCompany
from app.models.platform_user import PlatformUser
from app.models.settlement_payout import SettlementPayout
from app.rbac.permissions import Permission
from app.schemas.settlement import SettlementPayoutOut
from app.services import settlement_service

router = APIRouter(prefix="/settlements", tags=["settlements"])


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
