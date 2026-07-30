from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import InstallmentStatus
from app.models.platform_user import PlatformUser
from app.models.premium_installment import PremiumInstallment
from app.services.audit_service import record_audit_log


async def flag_overdue_installments(db: AsyncSession) -> int:
    """due_date < today AND status = due -> overdue (PRD §7). Purely a
    visibility flip for reporting/reminders — never charges anything.
    """
    today = date.today()
    installments = await db.scalars(
        select(PremiumInstallment).where(
            PremiumInstallment.due_date < today,
            PremiumInstallment.status == InstallmentStatus.DUE.value,
        )
    )
    count = 0
    for installment in installments:
        installment.status = InstallmentStatus.OVERDUE.value
        await record_audit_log(
            db,
            action="premium_installment.flagged_overdue",
            entity_type="premium_installment",
            entity_id=installment.id,
            before_state={"status": InstallmentStatus.DUE.value},
            after_state={"status": InstallmentStatus.OVERDUE.value},
        )
        count += 1
    await db.flush()
    return count


def actionable_overdue_cutoff_date(*, today: date, grace_period_days: int) -> date:
    """due_date values on/after this cutoff are within the grace window and
    excluded from insurer-facing overdue surfaces -- purely a display/action
    filter, never touches PremiumInstallment.status.
    """
    return today - timedelta(days=grace_period_days)


async def set_reference_number(
    db: AsyncSession,
    *,
    installment: PremiumInstallment,
    reference_number: str | None,
    actor: PlatformUser,
) -> PremiumInstallment:
    """A real, externally-sourced Debit Note / reference number entered by
    a broker or insurer against one specific premium installment -- e.g.
    once the insurer's own system has issued a debit note for it. Purely a
    labeling action; never changes payment/installment status.
    """
    before = {"reference_number": installment.reference_number}
    installment.reference_number = reference_number.strip() if reference_number else None
    await record_audit_log(
        db,
        action="premium_installment.reference_number_set",
        entity_type="premium_installment",
        entity_id=installment.id,
        actor_id=actor.id,
        actor_role=actor.role,
        before_state=before,
        after_state={"reference_number": installment.reference_number},
    )
    await db.flush()
    return installment
