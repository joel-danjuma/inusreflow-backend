import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import get_current_user, get_tenant_id, require_permission
from app.models.platform_user import PlatformUser
from app.models.policy import Policy
from app.models.premium_installment import PremiumInstallment
from app.models.reminder import Reminder
from app.rbac.permissions import Permission, Role
from app.schemas.policy import ReminderCreateRequest, ReminderOut
from app.services import installment_service, reminder_service
from app.workers.tasks.reminder_tasks import send_reminder_email_task

router = APIRouter(prefix="/reminders", tags=["reminders"])


class BulkReminderResult(BaseModel):
    reminders_created: int


@router.post("", response_model=ReminderOut, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    payload: ReminderCreateRequest,
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.SEND_REMINDER))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReminderOut:
    reminder = await reminder_service.create_reminder(
        db, actor=actor, installment_id=payload.installment_id
    )
    send_reminder_email_task.delay(str(reminder.id))
    return ReminderOut.model_validate(reminder)


@router.post("/bulk", response_model=BulkReminderResult, status_code=status.HTTP_201_CREATED)
async def create_bulk_reminders(
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.SEND_REMINDER))],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BulkReminderResult:
    """Queues one reminder per installment overdue past the grace period
    under the caller's tenant, reusing create_reminder per installment (same
    audit logging/dispatch as a single reminder) rather than a separate
    write path.
    """
    settings = get_settings()
    overdue_cutoff = installment_service.actionable_overdue_cutoff_date(
        today=datetime.now(UTC).date(), grace_period_days=settings.overdue_grace_period_days
    )
    stmt = (
        select(PremiumInstallment.id)
        .join(Policy, PremiumInstallment.policy_id == Policy.id)
        .where(
            PremiumInstallment.status == "overdue",
            PremiumInstallment.due_date < overdue_cutoff,
        )
    )
    if tenant_id is not None:
        stmt = stmt.where(Policy.insurance_company_id == tenant_id)
    installment_ids = (await db.scalars(stmt)).all()

    for installment_id in installment_ids:
        reminder = await reminder_service.create_reminder(
            db, actor=actor, installment_id=installment_id
        )
        send_reminder_email_task.delay(str(reminder.id))

    return BulkReminderResult(reminders_created=len(installment_ids))


@router.get("", response_model=list[ReminderOut])
async def list_reminders(
    broker_id: uuid.UUID,
    actor: Annotated[PlatformUser, Depends(get_current_user)],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ReminderOut]:
    role = Role(actor.role)
    if role in (Role.BROKER_ADMIN, Role.BROKER_STAFF) and actor.broker_id != broker_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    stmt = (
        select(Reminder)
        .join(PremiumInstallment, Reminder.installment_id == PremiumInstallment.id)
        .join(Policy, PremiumInstallment.policy_id == Policy.id)
        .where(Reminder.broker_id == broker_id)
    )
    if tenant_id is not None:
        stmt = stmt.where(Policy.insurance_company_id == tenant_id)
    result = await db.scalars(stmt)
    return [ReminderOut.model_validate(r) for r in result.all()]
