from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import InstallmentStatus
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
