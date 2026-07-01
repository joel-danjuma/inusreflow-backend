import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import require_permission
from app.models.broker import Broker
from app.models.insurance_company import InsuranceCompany
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Permission
from app.schemas.onboarding import (
    ApprovalResult,
    AssignBrokerInsurerRequest,
    BrokerInsurerAssignmentOut,
    BrokerOut,
    InsuranceCompanyOut,
    RejectRequest,
)
from app.services import onboarding_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/insurance-companies", response_model=list[InsuranceCompanyOut])
async def list_insurance_companies(
    _: Annotated[
        PlatformUser, Depends(require_permission(Permission.VIEW_ALL_INSURANCE_COMPANIES))
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[InsuranceCompanyOut]:
    companies = await db.scalars(select(InsuranceCompany))
    return [InsuranceCompanyOut.model_validate(c) for c in companies]


@router.patch("/insurance-companies/{company_id}/approve", response_model=ApprovalResult)
async def approve_insurance_company(
    company_id: uuid.UUID,
    actor: Annotated[
        PlatformUser, Depends(require_permission(Permission.APPROVE_INSURANCE_COMPANY))
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApprovalResult:
    _, raw_token = await onboarding_service.approve_insurance_company(
        db, company_id=company_id, actor=actor
    )
    return ApprovalResult(activation_token=raw_token)


@router.patch("/insurance-companies/{company_id}/reject", response_model=InsuranceCompanyOut)
async def reject_insurance_company(
    company_id: uuid.UUID,
    payload: RejectRequest,
    actor: Annotated[
        PlatformUser, Depends(require_permission(Permission.APPROVE_INSURANCE_COMPANY))
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InsuranceCompanyOut:
    company = await onboarding_service.reject_insurance_company(
        db, company_id=company_id, reason=payload.reason, actor=actor
    )
    return InsuranceCompanyOut.model_validate(company)


@router.get("/brokers", response_model=list[BrokerOut])
async def list_brokers(
    _: Annotated[PlatformUser, Depends(require_permission(Permission.VIEW_ALL_BROKERS))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[BrokerOut]:
    brokers = await db.scalars(select(Broker))
    return [BrokerOut.model_validate(b) for b in brokers]


@router.patch("/brokers/{broker_id}/approve", response_model=ApprovalResult)
async def approve_broker(
    broker_id: uuid.UUID,
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.APPROVE_BROKER))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApprovalResult:
    _, raw_token = await onboarding_service.approve_broker(db, broker_id=broker_id, actor=actor)
    return ApprovalResult(activation_token=raw_token)


@router.patch("/brokers/{broker_id}/reject", response_model=BrokerOut)
async def reject_broker(
    broker_id: uuid.UUID,
    payload: RejectRequest,
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.APPROVE_BROKER))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BrokerOut:
    broker = await onboarding_service.reject_broker(
        db, broker_id=broker_id, reason=payload.reason, actor=actor
    )
    return BrokerOut.model_validate(broker)


@router.post(
    "/brokers/{broker_id}/assign-insurer",
    response_model=BrokerInsurerAssignmentOut,
    status_code=status.HTTP_201_CREATED,
)
async def assign_broker_to_insurer(
    broker_id: uuid.UUID,
    payload: AssignBrokerInsurerRequest,
    actor: Annotated[
        PlatformUser, Depends(require_permission(Permission.ASSIGN_BROKER_TO_INSURER))
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BrokerInsurerAssignmentOut:
    assignment = await onboarding_service.assign_broker_to_insurer(
        db, broker_id=broker_id, insurance_company_id=payload.insurance_company_id, actor=actor
    )
    return BrokerInsurerAssignmentOut.model_validate(assignment)
