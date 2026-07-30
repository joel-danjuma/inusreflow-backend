import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import get_squad_client, require_permission
from app.integrations.squad.client import SquadClient
from app.models.audit import AuditLog
from app.models.broker import Broker
from app.models.broker_insurer_assignment import BrokerInsurerAssignment
from app.models.insurance_company import InsuranceCompany
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Permission
from app.schemas.audit import AuditLogOut
from app.schemas.onboarding import (
    AssignBrokerInsurerRequest,
    BrokerInsurerAssignmentOut,
    BrokerOut,
    InsuranceCompanyOut,
    OtpResult,
    RejectRequest,
    SetParentCompanyRequest,
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


@router.patch("/insurance-companies/{company_id}/approve", response_model=InsuranceCompanyOut)
async def approve_insurance_company(
    company_id: uuid.UUID,
    actor: Annotated[
        PlatformUser, Depends(require_permission(Permission.APPROVE_INSURANCE_COMPANY))
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InsuranceCompanyOut:
    company = await onboarding_service.approve_insurance_company(
        db, company_id=company_id, actor=actor
    )
    return InsuranceCompanyOut.model_validate(company)


@router.patch("/insurance-companies/{company_id}/reissue-otp", response_model=OtpResult)
async def reissue_insurance_company_otp(
    company_id: uuid.UUID,
    actor: Annotated[
        PlatformUser, Depends(require_permission(Permission.APPROVE_INSURANCE_COMPANY))
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OtpResult:
    raw_otp = await onboarding_service.reissue_insurance_company_otp(
        db, company_id=company_id, actor=actor
    )
    return OtpResult(otp=raw_otp)


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


@router.patch("/insurance-companies/{company_id}/set-parent", response_model=InsuranceCompanyOut)
async def set_insurance_company_parent(
    company_id: uuid.UUID,
    payload: SetParentCompanyRequest,
    actor: Annotated[
        PlatformUser, Depends(require_permission(Permission.MANAGE_INSURANCE_COMPANY_HIERARCHY))
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InsuranceCompanyOut:
    company = await onboarding_service.set_insurance_company_parent(
        db, company_id=company_id, parent_company_id=payload.parent_company_id, actor=actor
    )
    return InsuranceCompanyOut.model_validate(company)


@router.get("/brokers", response_model=list[BrokerOut])
async def list_brokers(
    _: Annotated[PlatformUser, Depends(require_permission(Permission.VIEW_ALL_BROKERS))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[BrokerOut]:
    brokers = await db.scalars(select(Broker))
    return [BrokerOut.model_validate(b) for b in brokers]


@router.patch("/brokers/{broker_id}/approve", response_model=BrokerOut)
async def approve_broker(
    broker_id: uuid.UUID,
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.APPROVE_BROKER))],
    db: Annotated[AsyncSession, Depends(get_db)],
    squad_client: Annotated[SquadClient, Depends(get_squad_client)],
) -> BrokerOut:
    settings = get_settings()
    broker = await onboarding_service.approve_broker(
        db,
        broker_id=broker_id,
        actor=actor,
        squad_client=squad_client,
        beneficiary_account=settings.squad_beneficiary_account,
    )
    return BrokerOut.model_validate(broker)


@router.patch("/brokers/{broker_id}/reissue-otp", response_model=OtpResult)
async def reissue_broker_otp(
    broker_id: uuid.UUID,
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.APPROVE_BROKER))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OtpResult:
    raw_otp = await onboarding_service.reissue_broker_otp(db, broker_id=broker_id, actor=actor)
    return OtpResult(otp=raw_otp)


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


@router.delete(
    "/brokers/{broker_id}/assign-insurer/{insurance_company_id}",
    response_model=BrokerInsurerAssignmentOut,
)
async def unassign_broker_from_insurer(
    broker_id: uuid.UUID,
    insurance_company_id: uuid.UUID,
    actor: Annotated[
        PlatformUser, Depends(require_permission(Permission.ASSIGN_BROKER_TO_INSURER))
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BrokerInsurerAssignmentOut:
    assignment = await onboarding_service.unassign_broker_from_insurer(
        db, broker_id=broker_id, insurance_company_id=insurance_company_id, actor=actor
    )
    return BrokerInsurerAssignmentOut.model_validate(assignment)


@router.get("/brokers/{broker_id}/assignments", response_model=list[BrokerInsurerAssignmentOut])
async def list_broker_assignments(
    broker_id: uuid.UUID,
    _: Annotated[PlatformUser, Depends(require_permission(Permission.VIEW_ALL_BROKERS))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[BrokerInsurerAssignmentOut]:
    """Every assignment this broker has ever had, active and historical --
    admin-only visibility into the many-to-many graph (no such view existed
    before many-to-many, since there was never more than one row worth
    inspecting per broker at a time).
    """
    assignments = await db.scalars(
        select(BrokerInsurerAssignment)
        .where(BrokerInsurerAssignment.broker_id == broker_id)
        .order_by(BrokerInsurerAssignment.assigned_at.desc())
    )
    return [BrokerInsurerAssignmentOut.model_validate(a) for a in assignments]


@router.get("/audit-logs", response_model=list[AuditLogOut])
async def list_audit_logs(
    _: Annotated[PlatformUser, Depends(require_permission(Permission.VIEW_AUDIT_LOGS))],
    db: Annotated[AsyncSession, Depends(get_db)],
    entity_type: Annotated[str | None, Query()] = None,
    action: Annotated[str | None, Query()] = None,
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(le=200)] = 50,
    offset: Annotated[int, Query()] = 0,
) -> list[AuditLogOut]:
    """Insureflow-Admin-only, cross-tenant by design (AuditLog has no
    insurance_company_id column). Paginated since audit_logs is insert-only
    with indefinite retention (docs/adr/0010-audit-log-retention.md).
    """
    stmt = select(AuditLog)
    if entity_type is not None:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if action is not None:
        stmt = stmt.where(AuditLog.action == action)
    if date_from is not None:
        stmt = stmt.where(AuditLog.created_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(AuditLog.created_at <= date_to)
    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)

    result = await db.scalars(stmt)
    return [AuditLogOut.model_validate(a) for a in result.all()]
