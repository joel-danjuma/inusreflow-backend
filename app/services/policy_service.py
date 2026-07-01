import calendar
import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.enums import InstallmentStatus, PolicyStatus, PremiumFrequency
from app.models.platform_user import PlatformUser
from app.models.policy import DEFAULT_POLICY_TYPE, Policy
from app.models.policyholder import Policyholder
from app.models.premium_installment import PremiumInstallment
from app.services.audit_service import record_audit_log

# Rolling window size, not the policy's full lifetime schedule (PRD §7 /
# CLAUDE.md) — top_up_policy_installments keeps this topped up as
# installments resolve, instead of generating years of rows upfront.
INSTALLMENT_WINDOW_SIZE = 12

_FREQUENCY_MONTHS: dict[PremiumFrequency, int] = {
    PremiumFrequency.MONTHLY: 1,
    PremiumFrequency.QUARTERLY: 3,
    PremiumFrequency.ANNUALLY: 12,
}


def _add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _generate_due_dates(start_date: date, frequency: PremiumFrequency, count: int) -> list[date]:
    """The first installment is due at policy inception (start_date itself),
    then recurs every `frequency` interval after that.
    """
    step = _FREQUENCY_MONTHS[frequency]
    return [_add_months(start_date, step * i) for i in range(count)]


async def create_policyholder(
    db: AsyncSession,
    *,
    actor: PlatformUser,
    insurance_company_id: uuid.UUID,
    full_name: str,
    email: str | None,
    phone_number: str | None,
    identification_number: str | None,
) -> Policyholder:
    policyholder = Policyholder(
        broker_id=actor.broker_id,
        insurance_company_id=insurance_company_id,
        full_name=full_name,
        email=email,
        phone_number=phone_number,
        identification_number=identification_number,
    )
    db.add(policyholder)
    await db.flush()

    await record_audit_log(
        db,
        action="policyholder.created",
        entity_type="policyholder",
        entity_id=policyholder.id,
        actor_id=actor.id,
        actor_role=actor.role,
        after_state={"full_name": full_name, "broker_id": str(actor.broker_id)},
    )
    await db.flush()
    return policyholder


async def create_policy(
    db: AsyncSession,
    *,
    actor: PlatformUser,
    insurance_company_id: uuid.UUID,
    policyholder_id: uuid.UUID,
    premium_amount_kobo: int,
    premium_frequency: PremiumFrequency,
    start_date: date,
    policy_type: str = DEFAULT_POLICY_TYPE,
) -> Policy:
    """policyholder_id is a request-body reference, not a URL path resource —
    treating a cross-broker mismatch as NotFound (rather than Forbidden)
    avoids confirming another broker's policyholder ID exists.
    """
    policyholder = await db.get(Policyholder, policyholder_id)
    if policyholder is None or policyholder.broker_id != actor.broker_id:
        raise NotFoundError("policyholder not found")

    policy = Policy(
        policyholder_id=policyholder_id,
        broker_id=actor.broker_id,
        insurance_company_id=insurance_company_id,
        policy_type=policy_type,
        premium_amount_kobo=premium_amount_kobo,
        premium_frequency=premium_frequency.value,
        start_date=start_date,
    )
    db.add(policy)
    await db.flush()

    for due_date in _generate_due_dates(start_date, premium_frequency, INSTALLMENT_WINDOW_SIZE):
        db.add(
            PremiumInstallment(
                policy_id=policy.id, due_date=due_date, amount_kobo=premium_amount_kobo
            )
        )

    await record_audit_log(
        db,
        action="policy.created",
        entity_type="policy",
        entity_id=policy.id,
        actor_id=actor.id,
        actor_role=actor.role,
        after_state={
            "policyholder_id": str(policyholder_id),
            "premium_amount_kobo": premium_amount_kobo,
            "premium_frequency": premium_frequency.value,
        },
    )
    await db.flush()
    return policy


async def top_up_policy_installments(db: AsyncSession, policy: Policy) -> int:
    """Maintains a rolling window of INSTALLMENT_WINDOW_SIZE unresolved
    (due/overdue) installments per active policy by topping up only the
    shortfall, rather than ever regenerating the full schedule.
    """
    if policy.status != PolicyStatus.ACTIVE.value:
        return 0

    unresolved_count = await db.scalar(
        select(func.count())
        .select_from(PremiumInstallment)
        .where(
            PremiumInstallment.policy_id == policy.id,
            PremiumInstallment.status.in_(
                [InstallmentStatus.DUE.value, InstallmentStatus.OVERDUE.value]
            ),
        )
    )
    shortfall = INSTALLMENT_WINDOW_SIZE - (unresolved_count or 0)
    if shortfall <= 0:
        return 0

    latest_due_date = await db.scalar(
        select(func.max(PremiumInstallment.due_date)).where(
            PremiumInstallment.policy_id == policy.id
        )
    )
    base_date = latest_due_date if latest_due_date is not None else policy.start_date
    step = _FREQUENCY_MONTHS[PremiumFrequency(policy.premium_frequency)]
    for i in range(1, shortfall + 1):
        db.add(
            PremiumInstallment(
                policy_id=policy.id,
                due_date=_add_months(base_date, step * i),
                amount_kobo=policy.premium_amount_kobo,
            )
        )
    await db.flush()
    return shortfall


async def top_up_all_active_policies(db: AsyncSession) -> int:
    policies = await db.scalars(select(Policy).where(Policy.status == PolicyStatus.ACTIVE.value))
    total = 0
    for policy in policies:
        total += await top_up_policy_installments(db, policy)
    return total
