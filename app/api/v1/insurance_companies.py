import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user, get_squad_client, require_permission
from app.integrations.squad.client import SquadClient
from app.models.insurance_company import InsuranceCompany
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Permission, Role
from app.schemas.onboarding import (
    InsuranceCompanyOnboardRequest,
    InsuranceCompanyOut,
    SettlementAccountSetRequest,
)
from app.services import onboarding_service

router = APIRouter(prefix="/insurance-companies", tags=["insurance-companies"])


@router.post("", response_model=InsuranceCompanyOut, status_code=status.HTTP_201_CREATED)
async def onboard_insurance_company(
    payload: InsuranceCompanyOnboardRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InsuranceCompanyOut:
    company = await onboarding_service.onboard_insurance_company(
        db, name=payload.name, contact_email=payload.contact_email
    )
    return InsuranceCompanyOut.model_validate(company)


@router.get("/{company_id}", response_model=InsuranceCompanyOut)
async def get_insurance_company(
    company_id: uuid.UUID,
    user: Annotated[PlatformUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InsuranceCompanyOut:
    if Role(user.role) is not Role.INSUREFLOW_ADMIN and user.insurance_company_id != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    company = await db.get(InsuranceCompany, company_id)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="insurance company not found"
        )
    return InsuranceCompanyOut.model_validate(company)


@router.post("/{company_id}/settlement-account", response_model=InsuranceCompanyOut)
async def set_settlement_account(
    company_id: uuid.UUID,
    payload: SettlementAccountSetRequest,
    actor: Annotated[
        PlatformUser, Depends(require_permission(Permission.MANAGE_OWN_INSURANCE_COMPANY))
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
    squad_client: Annotated[SquadClient, Depends(get_squad_client)],
) -> InsuranceCompanyOut:
    if actor.insurance_company_id != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    company = await onboarding_service.set_insurer_settlement_account(
        db,
        company_id=company_id,
        bank_code=payload.bank_code,
        account_number=payload.account_number,
        squad_client=squad_client,
        actor=actor,
    )
    return InsuranceCompanyOut.model_validate(company)
