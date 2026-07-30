import uuid
from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import (
    get_current_user,
    get_insurer_broker_filter,
    get_own_insurer_id,
    get_squad_client,
    require_permission,
)
from app.integrations.squad.client import SquadClient
from app.models.broker import Broker
from app.models.broker_insurer_assignment import BrokerInsurerAssignment
from app.models.insurance_company import InsuranceCompany
from app.models.ledger_account import LedgerAccount
from app.models.ledger_entry import LedgerEntry
from app.models.payment import Payment
from app.models.payment_batch import PaymentBatch
from app.models.payment_batch_item import PaymentBatchItem
from app.models.platform_user import PlatformUser
from app.models.policy import Policy
from app.models.policyholder import Policyholder
from app.models.premium_installment import PremiumInstallment
from app.rbac.permissions import Permission, Role
from app.schemas.insurer_dashboard import (
    BrokerPerformanceOut,
    InsurerDashboardSummary,
    LatestPaymentOut,
    OutstandingPolicyOut,
    RecentPolicyOut,
)
from app.schemas.onboarding import (
    BrokerOut,
    InsuranceCompanyOnboardRequest,
    InsuranceCompanyOnboardResult,
    InsuranceCompanyOut,
    SettlementAccountSetRequest,
)
from app.services import installment_service, onboarding_service

router = APIRouter(prefix="/insurance-companies", tags=["insurance-companies"])

_RECENT_LIST_LIMIT = 10
_OUTSTANDING_LIST_LIMIT = 50


def _policy_number(policy_id: uuid.UUID) -> str:
    """No policy_number column exists (CLAUDE.md keeps policies schema-open,
    open string policy_type) -- this is a stable, honest display derived
    from the real id, never a fabricated sequence.
    """
    return f"POL-{str(policy_id)[:8].upper()}"


@router.post("", response_model=InsuranceCompanyOnboardResult, status_code=status.HTTP_201_CREATED)
async def onboard_insurance_company(
    payload: InsuranceCompanyOnboardRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InsuranceCompanyOnboardResult:
    company, raw_otp = await onboarding_service.onboard_insurance_company(
        db, name=payload.name, contact_email=payload.contact_email
    )
    return InsuranceCompanyOnboardResult(
        company=InsuranceCompanyOut.model_validate(company), otp=raw_otp
    )


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


@router.get("/{company_id}/brokers", response_model=list[BrokerOut])
async def list_insurance_company_brokers(
    company_id: uuid.UUID,
    user: Annotated[PlatformUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[BrokerOut]:
    """Brokers actively assigned to this insurer -- e.g. for populating a
    broker picker when an Insurance Company Admin sets a broker-scoped
    commission rate. insureflow_admin may view any insurer's; an Insurance
    Company Admin only their own.
    """
    if Role(user.role) is not Role.INSUREFLOW_ADMIN and user.insurance_company_id != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    stmt = (
        select(Broker)
        .join(BrokerInsurerAssignment, BrokerInsurerAssignment.broker_id == Broker.id)
        .where(
            BrokerInsurerAssignment.insurance_company_id == company_id,
            BrokerInsurerAssignment.is_active.is_(True),
        )
    )
    result = await db.scalars(stmt)
    return [BrokerOut.model_validate(b) for b in result.all()]


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


@router.get("/me/dashboard-summary", response_model=InsurerDashboardSummary)
async def get_own_dashboard_summary(
    company_id: Annotated[uuid.UUID, Depends(get_own_insurer_id)],
    broker_id: Annotated[uuid.UUID | None, Depends(get_insurer_broker_filter)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InsurerDashboardSummary:
    settings = get_settings()
    now = datetime.now(UTC)
    month_start = date(now.year, now.month, 1)
    overdue_cutoff = installment_service.actionable_overdue_cutoff_date(
        today=now.date(), grace_period_days=settings.overdue_grace_period_days
    )

    new_policies_stmt = select(func.count()).select_from(Policy).where(
        Policy.insurance_company_id == company_id, Policy.created_at >= month_start
    )
    if broker_id is not None:
        new_policies_stmt = new_policies_stmt.where(Policy.broker_id == broker_id)
    new_policies_count = await db.scalar(new_policies_stmt) or 0

    outstanding_stmt = (
        select(func.coalesce(func.sum(PremiumInstallment.amount_kobo), 0))
        .select_from(PremiumInstallment)
        .join(Policy, PremiumInstallment.policy_id == Policy.id)
        .where(
            Policy.insurance_company_id == company_id,
            PremiumInstallment.status.in_(["due", "overdue"]),
        )
    )
    if broker_id is not None:
        outstanding_stmt = outstanding_stmt.where(Policy.broker_id == broker_id)
    outstanding_premiums_kobo = await db.scalar(outstanding_stmt) or 0

    brokers_count_stmt = (
        select(func.count())
        .select_from(BrokerInsurerAssignment)
        .where(
            BrokerInsurerAssignment.insurance_company_id == company_id,
            BrokerInsurerAssignment.is_active.is_(True),
        )
    )
    if broker_id is not None:
        brokers_count_stmt = brokers_count_stmt.where(
            BrokerInsurerAssignment.broker_id == broker_id
        )
    total_brokers_count = await db.scalar(brokers_count_stmt) or 0

    overdue_stmt = (
        select(func.count(func.distinct(PremiumInstallment.policy_id)))
        .select_from(PremiumInstallment)
        .join(Policy, PremiumInstallment.policy_id == Policy.id)
        .where(
            Policy.insurance_company_id == company_id,
            PremiumInstallment.status == "overdue",
            PremiumInstallment.due_date < overdue_cutoff,
        )
    )
    if broker_id is not None:
        overdue_stmt = overdue_stmt.where(Policy.broker_id == broker_id)
    overdue_policies_count = await db.scalar(overdue_stmt) or 0

    return InsurerDashboardSummary(
        new_policies_count=new_policies_count,
        outstanding_premiums_kobo=outstanding_premiums_kobo,
        total_brokers_count=total_brokers_count,
        overdue_policies_count=overdue_policies_count,
    )


async def _latest_payment_dates(
    db: AsyncSession, policy_ids: list[uuid.UUID]
) -> dict[uuid.UUID, date]:
    """Most recent successful-payment date per policy, across every
    installment (paid singly or via a bulk batch) that policy has ever had
    -- not just its currently-overdue one.
    """
    if not policy_ids:
        return {}

    paid_rows = (
        await db.execute(
            select(
                PremiumInstallment.policy_id,
                PremiumInstallment.payment_id,
                PremiumInstallment.payment_batch_item_id,
            ).where(
                PremiumInstallment.policy_id.in_(policy_ids), PremiumInstallment.status == "paid"
            )
        )
    ).all()
    if not paid_rows:
        return {}

    payment_ids = [r.payment_id for r in paid_rows if r.payment_id is not None]
    batch_item_ids = [
        r.payment_batch_item_id for r in paid_rows if r.payment_batch_item_id is not None
    ]

    payment_dates: dict[uuid.UUID, datetime] = {}
    if payment_ids:
        rows = await db.execute(
            select(Payment.id, Payment.updated_at).where(Payment.id.in_(payment_ids))
        )
        payment_dates = {row.id: row.updated_at for row in rows}

    batch_item_dates: dict[uuid.UUID, datetime] = {}
    if batch_item_ids:
        item_to_batch_rows = await db.execute(
            select(PaymentBatchItem.id, PaymentBatchItem.payment_batch_id).where(
                PaymentBatchItem.id.in_(batch_item_ids)
            )
        )
        item_to_batch: dict[uuid.UUID, uuid.UUID] = {
            row.id: row.payment_batch_id for row in item_to_batch_rows
        }
        batch_ids = list(set(item_to_batch.values()))
        batch_date_rows = await db.execute(
            select(PaymentBatch.id, PaymentBatch.updated_at).where(PaymentBatch.id.in_(batch_ids))
        )
        batch_dates: dict[uuid.UUID, datetime] = {row.id: row.updated_at for row in batch_date_rows}
        batch_item_dates = {
            item_id: batch_dates[batch_id]
            for item_id, batch_id in item_to_batch.items()
            if batch_id in batch_dates
        }

    latest: dict[uuid.UUID, datetime] = {}
    for row in paid_rows:
        resolved = (
            payment_dates.get(row.payment_id)
            if row.payment_id is not None
            else batch_item_dates.get(row.payment_batch_item_id)
        )
        if resolved is None:
            continue
        if row.policy_id not in latest or resolved > latest[row.policy_id]:
            latest[row.policy_id] = resolved

    return {policy_id: dt.date() for policy_id, dt in latest.items()}


@router.get("/me/outstanding-policies", response_model=list[OutstandingPolicyOut])
async def list_own_outstanding_policies(
    company_id: Annotated[uuid.UUID, Depends(get_own_insurer_id)],
    broker_id: Annotated[uuid.UUID | None, Depends(get_insurer_broker_filter)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[OutstandingPolicyOut]:
    """One row per policy -- its single most-overdue (oldest due date)
    installment past the grace period, worst-first, capped for a collapsible
    dashboard section rather than fully paginated.
    """
    settings = get_settings()
    today = datetime.now(UTC).date()
    overdue_cutoff = installment_service.actionable_overdue_cutoff_date(
        today=today, grace_period_days=settings.overdue_grace_period_days
    )

    stmt = (
        select(PremiumInstallment, Policy, Policyholder.full_name, Broker.name)
        .join(Policy, PremiumInstallment.policy_id == Policy.id)
        .join(Policyholder, Policy.policyholder_id == Policyholder.id)
        .join(Broker, Policy.broker_id == Broker.id)
        .where(
            Policy.insurance_company_id == company_id,
            PremiumInstallment.status == "overdue",
            PremiumInstallment.due_date < overdue_cutoff,
        )
        .order_by(PremiumInstallment.policy_id, PremiumInstallment.due_date)
        .distinct(PremiumInstallment.policy_id)
    )
    if broker_id is not None:
        stmt = stmt.where(Policy.broker_id == broker_id)
    rows = (await db.execute(stmt)).all()
    rows = sorted(rows, key=lambda r: r[0].due_date)[:_OUTSTANDING_LIST_LIMIT]

    last_payment_dates = await _latest_payment_dates(db, [policy.id for _, policy, _, _ in rows])

    return [
        OutstandingPolicyOut(
            policy_id=policy.id,
            policy_number=_policy_number(policy.id),
            customer_name=full_name,
            broker_name=broker_name,
            premium_amount_kobo=installment.amount_kobo,
            days_overdue=(today - installment.due_date).days - settings.overdue_grace_period_days,
            last_payment_date=last_payment_dates.get(policy.id),
            reference_number=installment.reference_number,
        )
        for installment, policy, full_name, broker_name in rows
    ]


@router.get("/me/recent-policies", response_model=list[RecentPolicyOut])
async def list_own_recent_policies(
    company_id: Annotated[uuid.UUID, Depends(get_own_insurer_id)],
    broker_id: Annotated[uuid.UUID | None, Depends(get_insurer_broker_filter)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[RecentPolicyOut]:
    stmt = (
        select(Policy, Policyholder.full_name, Broker.name)
        .join(Policyholder, Policy.policyholder_id == Policyholder.id)
        .join(Broker, Policy.broker_id == Broker.id)
        .where(Policy.insurance_company_id == company_id)
        .order_by(Policy.created_at.desc())
        .limit(_RECENT_LIST_LIMIT)
    )
    if broker_id is not None:
        stmt = stmt.where(Policy.broker_id == broker_id)
    rows = (await db.execute(stmt)).all()

    return [
        RecentPolicyOut(
            policy_id=policy.id,
            policy_number=_policy_number(policy.id),
            customer_name=full_name,
            broker_name=broker_name,
            policy_amount_kobo=policy.premium_amount_kobo,
            created_at=policy.created_at,
        )
        for policy, full_name, broker_name in rows
    ]


@router.get("/me/broker-performance", response_model=list[BrokerPerformanceOut])
async def list_own_broker_performance(
    company_id: Annotated[uuid.UUID, Depends(get_own_insurer_id)],
    broker_id: Annotated[uuid.UUID | None, Depends(get_insurer_broker_filter)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[BrokerPerformanceOut]:
    brokers_stmt = (
        select(Broker.id, Broker.name)
        .join(BrokerInsurerAssignment, BrokerInsurerAssignment.broker_id == Broker.id)
        .where(
            BrokerInsurerAssignment.insurance_company_id == company_id,
            BrokerInsurerAssignment.is_active.is_(True),
        )
    )
    if broker_id is not None:
        brokers_stmt = brokers_stmt.where(BrokerInsurerAssignment.broker_id == broker_id)
    brokers = (await db.execute(brokers_stmt)).all()
    broker_ids = [b.id for b in brokers]
    if not broker_ids:
        return []

    policy_count_rows = await db.execute(
        select(Policy.broker_id, func.count())
        .where(Policy.insurance_company_id == company_id, Policy.broker_id.in_(broker_ids))
        .group_by(Policy.broker_id)
    )
    policy_counts: dict[uuid.UUID, int] = {row[0]: row[1] for row in policy_count_rows}

    commission_sum_rows = await db.execute(
        select(LedgerAccount.broker_id, func.coalesce(func.sum(LedgerEntry.amount_kobo), 0))
        .join(LedgerEntry, LedgerEntry.ledger_account_id == LedgerAccount.id)
        .where(
            LedgerAccount.account_type == "BROKER_COMMISSION",
            LedgerAccount.broker_id.in_(broker_ids),
            LedgerEntry.entry_type == "credit",
        )
        .group_by(LedgerAccount.broker_id)
    )
    commission_sums: dict[uuid.UUID | None, int] = {row[0]: row[1] for row in commission_sum_rows}

    performance = [
        BrokerPerformanceOut(
            broker_id=b.id,
            broker_name=b.name,
            policies_sold=policy_counts.get(b.id, 0),
            commission_earned_kobo=commission_sums.get(b.id, 0),
        )
        for b in brokers
    ]
    performance.sort(key=lambda p: p.commission_earned_kobo, reverse=True)
    return performance


@router.get("/me/latest-payments", response_model=list[LatestPaymentOut])
async def list_own_latest_payments(
    company_id: Annotated[uuid.UUID, Depends(get_own_insurer_id)],
    broker_id: Annotated[uuid.UUID | None, Depends(get_insurer_broker_filter)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=50)] = _RECENT_LIST_LIMIT,
) -> list[LatestPaymentOut]:
    """Unifies single Payments and bulk PaymentBatches into one feed -- Squad
    SVA bank transfer is the only collection method this product supports
    (docs/adr/0004), so payment_method is a constant, not a stored field.
    """
    singles_stmt = (
        select(Payment)
        .where(Payment.insurance_company_id == company_id)
        .order_by(Payment.created_at.desc())
        .limit(limit)
    )
    batches_stmt = (
        select(PaymentBatch)
        .where(PaymentBatch.insurance_company_id == company_id)
        .order_by(PaymentBatch.created_at.desc())
        .limit(limit)
    )
    if broker_id is not None:
        singles_stmt = singles_stmt.where(Payment.broker_id == broker_id)
        batches_stmt = batches_stmt.where(PaymentBatch.broker_id == broker_id)

    singles = (await db.execute(singles_stmt)).scalars().all()
    batches = (await db.execute(batches_stmt)).scalars().all()

    broker_ids = {p.broker_id for p in singles} | {b.broker_id for b in batches}
    broker_names: dict[uuid.UUID, str] = {}
    if broker_ids:
        broker_name_rows = await db.execute(
            select(Broker.id, Broker.name).where(Broker.id.in_(broker_ids))
        )
        broker_names = {row[0]: row[1] for row in broker_name_rows}

    combined = [
        LatestPaymentOut(
            id=p.id,
            broker_name=broker_names.get(p.broker_id, "Unknown broker"),
            total_amount_kobo=p.amount_kobo,
            policies_paid=1,
            payment_method="Bank Transfer",
            status=p.status,
            payment_date=p.created_at,
        )
        for p in singles
    ] + [
        LatestPaymentOut(
            id=b.id,
            broker_name=broker_names.get(b.broker_id, "Unknown broker"),
            total_amount_kobo=b.total_amount_kobo,
            policies_paid=b.item_count,
            payment_method="Bank Transfer",
            status=b.status,
            payment_date=b.created_at,
        )
        for b in batches
    ]
    combined.sort(key=lambda item: item.payment_date, reverse=True)
    return combined[:limit]
