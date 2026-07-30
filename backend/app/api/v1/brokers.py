import uuid
from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    get_broker_insurer_filter,
    get_current_user,
    get_tenant_id,
    require_permission,
)
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
from app.schemas.broker_dashboard import (
    BrokerDashboardSummary,
    BrokerPortfolioPage,
    MonthlyTrendPoint,
    PortfolioItemOut,
)
from app.schemas.onboarding import (
    BrokerOnboardRequest,
    BrokerOnboardResult,
    BrokerOut,
    CreateBrokerStaffRequest,
    InsuranceCompanyOut,
    OtpResult,
)
from app.services import onboarding_service

router = APIRouter(prefix="/brokers", tags=["brokers"])


def _require_broker_actor(actor: PlatformUser) -> uuid.UUID:
    if Role(actor.role) not in (Role.BROKER_ADMIN, Role.BROKER_STAFF) or actor.broker_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return actor.broker_id


def _last_n_month_keys(reference: date, n: int) -> list[str]:
    keys: list[str] = []
    year, month = reference.year, reference.month
    for _ in range(n):
        keys.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    return list(reversed(keys))


@router.post("", response_model=BrokerOnboardResult, status_code=status.HTTP_201_CREATED)
async def onboard_broker(
    payload: BrokerOnboardRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BrokerOnboardResult:
    broker, raw_otp = await onboarding_service.onboard_broker(
        db,
        name=payload.name,
        contact_email=payload.contact_email,
        bvn=payload.bvn,
        phone_number=payload.phone_number,
    )
    return BrokerOnboardResult(broker=BrokerOut.model_validate(broker), otp=raw_otp)


@router.get("/{broker_id}", response_model=BrokerOut)
async def get_broker(
    broker_id: uuid.UUID,
    user: Annotated[PlatformUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BrokerOut:
    if Role(user.role) is not Role.INSUREFLOW_ADMIN and user.broker_id != broker_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    broker = await db.get(Broker, broker_id)
    if broker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="broker not found")
    return BrokerOut.model_validate(broker)


@router.get("/{broker_id}/insurers", response_model=list[InsuranceCompanyOut])
async def list_broker_insurers(
    broker_id: uuid.UUID,
    user: Annotated[PlatformUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[InsuranceCompanyOut]:
    """Insurers actively assigned to this broker -- the mirror image of
    GET /insurance-companies/{company_id}/brokers, e.g. for populating the
    broker dashboard's insurer picker. insureflow_admin may view any
    broker's; a broker may only view their own.
    """
    if Role(user.role) is not Role.INSUREFLOW_ADMIN and user.broker_id != broker_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    stmt = (
        select(InsuranceCompany)
        .join(
            BrokerInsurerAssignment,
            BrokerInsurerAssignment.insurance_company_id == InsuranceCompany.id,
        )
        .where(
            BrokerInsurerAssignment.broker_id == broker_id,
            BrokerInsurerAssignment.is_active.is_(True),
        )
    )
    result = await db.scalars(stmt)
    return [InsuranceCompanyOut.model_validate(c) for c in result.all()]


@router.post(
    "/{broker_id}/staff", response_model=OtpResult, status_code=status.HTTP_201_CREATED
)
async def create_broker_staff(
    broker_id: uuid.UUID,
    payload: CreateBrokerStaffRequest,
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.MANAGE_BROKER_STAFF))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OtpResult:
    if actor.broker_id != broker_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    _, raw_otp = await onboarding_service.create_broker_staff_user(
        db, broker_id=broker_id, email=payload.email, actor=actor
    )
    return OtpResult(otp=raw_otp)


@router.get("/me/dashboard-summary", response_model=BrokerDashboardSummary)
async def get_own_dashboard_summary(
    actor: Annotated[PlatformUser, Depends(get_current_user)],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],  # noqa: ARG001 -- sets RLS context
    insurer_id: Annotated[uuid.UUID | None, Depends(get_broker_insurer_filter)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BrokerDashboardSummary:
    """Broker-only landing-page analytics -- never exposes raw ledger access
    (brokers don't hold VIEW_LEDGER, see CLAUDE.md's RBAC matrix), just the
    one commission total a broker is entitled to see about their own book.
    Aggregates across every insurer this broker works with by default;
    insurer_id narrows to one. The commission-total block below is
    deliberately unaffected by insurer_id -- BROKER_COMMISSION ledger
    accounts are keyed by broker_id alone, with no insurer dimension, since
    a broker's total commission is a broker-level figure.
    """
    broker_id = _require_broker_actor(actor)
    now = datetime.now(UTC)
    month_start = date(now.year, now.month, 1)

    single_stmt = select(Payment.amount_kobo, Payment.updated_at).where(
        Payment.broker_id == broker_id, Payment.status == "success"
    )
    batch_stmt = (
        select(PaymentBatchItem.amount_kobo, PaymentBatch.updated_at)
        .join(PaymentBatch, PaymentBatchItem.payment_batch_id == PaymentBatch.id)
        .where(PaymentBatch.broker_id == broker_id, PaymentBatch.status == "success")
    )
    if insurer_id is not None:
        single_stmt = single_stmt.where(Payment.insurance_company_id == insurer_id)
        batch_stmt = batch_stmt.where(PaymentBatch.insurance_company_id == insurer_id)

    single_rows = (await db.execute(single_stmt)).all()
    batch_rows = (await db.execute(batch_stmt)).all()

    total_kobo = sum(r.amount_kobo for r in single_rows) + sum(r.amount_kobo for r in batch_rows)
    this_month_kobo = sum(
        r.amount_kobo for r in single_rows if r.updated_at.date() >= month_start
    ) + sum(r.amount_kobo for r in batch_rows if r.updated_at.date() >= month_start)

    trend_buckets = dict.fromkeys(_last_n_month_keys(now.date(), 6), 0)
    for r in (*single_rows, *batch_rows):
        key = r.updated_at.strftime("%Y-%m")
        if key in trend_buckets:
            trend_buckets[key] += r.amount_kobo
    monthly_trends = [MonthlyTrendPoint(month=k, amount_kobo=v) for k, v in trend_buckets.items()]

    commission_account_id = await db.scalar(
        select(LedgerAccount.id).where(
            LedgerAccount.account_type == "BROKER_COMMISSION",
            LedgerAccount.broker_id == broker_id,
        )
    )
    total_commission_kobo = 0
    if commission_account_id is not None:
        total_commission_kobo = (
            await db.scalar(
                select(func.coalesce(func.sum(LedgerEntry.amount_kobo), 0)).where(
                    LedgerEntry.ledger_account_id == commission_account_id,
                    LedgerEntry.entry_type == "credit",
                )
            )
            or 0
        )

    policy_stmt = select(Policy.status, Policy.policyholder_id).where(Policy.broker_id == broker_id)
    if insurer_id is not None:
        policy_stmt = policy_stmt.where(Policy.insurance_company_id == insurer_id)
    policy_rows = (await db.execute(policy_stmt)).all()
    total_policies = len(policy_rows)
    active_policies = sum(1 for r in policy_rows if r.status == "active")
    retention_rate = (active_policies / total_policies * 100) if total_policies else 0.0
    active_clients_count = len({r.policyholder_id for r in policy_rows if r.status == "active"})

    return BrokerDashboardSummary(
        total_premiums_collected_kobo=total_kobo,
        total_premiums_this_month_kobo=this_month_kobo,
        total_commission_kobo=total_commission_kobo,
        client_retention_rate=round(retention_rate, 1),
        active_clients_count=active_clients_count,
        monthly_trends=monthly_trends,
    )


@router.get("/me/portfolio", response_model=BrokerPortfolioPage)
async def get_own_portfolio(
    actor: Annotated[PlatformUser, Depends(get_current_user)],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],  # noqa: ARG001 -- sets RLS context
    insurer_id: Annotated[uuid.UUID | None, Depends(get_broker_insurer_filter)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 10,
) -> BrokerPortfolioPage:
    """One row per (policyholder, policy) pair -- a client with two policies
    shows twice, since policy type/status are per-policy attributes. "Next
    payment" picks, per policy, the soonest due/overdue installment, falling
    back to the most recent one (implying paid-up) if none is outstanding.
    Aggregates across every insurer this broker works with by default;
    insurer_id narrows to one.
    """
    broker_id = _require_broker_actor(actor)

    total_stmt = select(func.count()).select_from(Policy).where(Policy.broker_id == broker_id)
    page_stmt = (
        select(Policy, Policyholder.full_name)
        .join(Policyholder, Policy.policyholder_id == Policyholder.id)
        .where(Policy.broker_id == broker_id)
        .order_by(Policyholder.full_name.asc(), Policy.created_at.asc())
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    if insurer_id is not None:
        total_stmt = total_stmt.where(Policy.insurance_company_id == insurer_id)
        page_stmt = page_stmt.where(Policy.insurance_company_id == insurer_id)

    total = await db.scalar(total_stmt) or 0
    page_rows = (await db.execute(page_stmt)).all()
    policy_ids = [policy.id for policy, _ in page_rows]

    next_installments: dict[uuid.UUID, PremiumInstallment] = {}
    if policy_ids:
        outstanding_first = case((PremiumInstallment.status.in_(["due", "overdue"]), 0), else_=1)
        installment_rows = await db.scalars(
            select(PremiumInstallment)
            .where(PremiumInstallment.policy_id.in_(policy_ids))
            .order_by(PremiumInstallment.policy_id, outstanding_first, PremiumInstallment.due_date)
            .distinct(PremiumInstallment.policy_id)
        )
        next_installments = {i.policy_id: i for i in installment_rows}

    # An outstanding "next" installment can already have a Payment/
    # PaymentBatchItem sitting at 'initiated' (started elsewhere -- another
    # staff member, a previous click, a bulk batch) -- initiate_payment
    # rejects a second attempt on the same installment (payment_service.py),
    # so Pay Now must never be offered for one of these, or the broker hits
    # a raw 409 with no explanation.
    outstanding_ids = [
        installment.id
        for installment in next_installments.values()
        if installment.status in ("due", "overdue")
    ]
    in_flight_ids: set[uuid.UUID] = set()
    if outstanding_ids:
        in_flight_ids.update(
            await db.scalars(
                select(Payment.installment_id).where(
                    Payment.installment_id.in_(outstanding_ids),
                    Payment.status == "initiated",
                )
            )
        )
        in_flight_ids.update(
            await db.scalars(
                select(PaymentBatchItem.installment_id)
                .join(PaymentBatch, PaymentBatchItem.payment_batch_id == PaymentBatch.id)
                .where(
                    PaymentBatchItem.installment_id.in_(outstanding_ids),
                    PaymentBatch.status == "initiated",
                )
            )
        )

    items: list[PortfolioItemOut] = []
    for policy, full_name in page_rows:
        installment = next_installments.get(policy.id)
        outstanding = installment is not None and installment.status in ("due", "overdue")
        in_flight = outstanding and installment is not None and installment.id in in_flight_ids

        if in_flight and installment is not None:
            payment_status, next_installment_id = "in_progress", None
        elif outstanding and installment is not None:
            payment_status, next_installment_id = installment.status, installment.id
        else:
            payment_status, next_installment_id = "paid", None

        items.append(
            PortfolioItemOut(
                policyholder_id=policy.policyholder_id,
                client_name=full_name,
                policy_id=policy.id,
                policy_type=policy.policy_type,
                policy_status=policy.status,
                premium_amount_kobo=policy.premium_amount_kobo,
                next_installment_id=next_installment_id,
                payment_status=payment_status,
                next_payment_date=installment.due_date if outstanding and installment else None,
                next_payment_reference_number=(
                    installment.reference_number if outstanding and installment else None
                ),
            )
        )

    return BrokerPortfolioPage(items=items, total=total, page=page, per_page=per_page)
