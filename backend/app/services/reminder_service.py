import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.enums import ReminderStatus
from app.models.platform_user import PlatformUser
from app.models.policy import Policy
from app.models.premium_installment import PremiumInstallment
from app.models.reminder import Reminder
from app.services.audit_service import record_audit_log


async def create_reminder(
    db: AsyncSession, *, actor: PlatformUser, installment_id: uuid.UUID
) -> Reminder:
    installment = await db.get(PremiumInstallment, installment_id)
    if installment is None:
        raise NotFoundError("installment not found")

    policy = await db.get(Policy, installment.policy_id)
    if policy is None or policy.insurance_company_id != actor.insurance_company_id:
        raise NotFoundError("installment not found")

    reminder = Reminder(installment_id=installment_id, broker_id=policy.broker_id, sent_by=actor.id)
    db.add(reminder)
    await db.flush()

    await record_audit_log(
        db,
        action="reminder.created",
        entity_type="reminder",
        entity_id=reminder.id,
        actor_id=actor.id,
        actor_role=actor.role,
        after_state={"installment_id": str(installment_id), "broker_id": str(policy.broker_id)},
    )
    await db.flush()
    return reminder


async def mark_reminder_sent(db: AsyncSession, *, reminder_id: uuid.UUID) -> Reminder:
    """Simulates dispatch — there's no real email infra yet (same gap
    onboarding's "activation token returned in the API response" workaround
    papers over). Flips status/sent_at as if delivery succeeded.
    """
    reminder = await db.get(Reminder, reminder_id)
    if reminder is None:
        raise NotFoundError("reminder not found")

    before = {"status": reminder.status}
    reminder.status = ReminderStatus.SENT.value
    reminder.sent_at = datetime.now(UTC)

    await record_audit_log(
        db,
        action="reminder.sent",
        entity_type="reminder",
        entity_id=reminder.id,
        before_state=before,
        after_state={"status": reminder.status},
    )
    await db.flush()
    return reminder
