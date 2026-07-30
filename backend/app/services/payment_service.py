import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, UnprocessableError
from app.core.metrics import payment_outcomes_total
from app.integrations.squad.client import SquadClient, generate_squad_ref
from app.integrations.squad.schemas import StaticVATransaction
from app.models.broker import Broker
from app.models.commission_config import CommissionConfig
from app.models.enums import InstallmentStatus, PaymentStatus
from app.models.insurance_company import InsuranceCompany
from app.models.payment import Payment
from app.models.payment_batch import PaymentBatch
from app.models.payment_batch_item import PaymentBatchItem
from app.models.platform_user import PlatformUser
from app.models.policy import Policy
from app.models.premium_installment import PremiumInstallment
from app.services import settlement_service
from app.services.audit_service import record_audit_log
from app.services.commission_service import calculate_split, resolve_commission_config
from app.services.ledger_service import (
    LedgerPosting,
    get_or_create_ledger_account,
    post_ledger_entries,
)

_TERMINAL_STATUSES = frozenset(
    {
        PaymentStatus.SUCCESS.value,
        PaymentStatus.MISMATCH.value,
        PaymentStatus.EXPIRED.value,
        PaymentStatus.FAILED.value,
    }
)

_logger = structlog.get_logger(__name__)


async def load_owned_installment_policy(
    db: AsyncSession, installment: PremiumInstallment, *, broker_id: uuid.UUID
) -> Policy:
    """An installment_id is just a UUID the caller supplies directly (never
    filtered server-side like GET /installments is) -- without this check any
    broker could pay off any other broker's installment. Raises NotFoundError
    rather than a 403 so probing random ids can't distinguish "doesn't exist"
    from "isn't yours".

    The policy this installment belongs to is also the unambiguous source of
    truth for which insurer this payment is attributed to -- a broker can now
    work with several insurers at once (many-to-many), so there is no longer
    a single caller-supplied insurance_company_id to trust or validate
    against; it's derived here instead, from the resource actually being
    paid for.
    """
    policy = await db.get(Policy, installment.policy_id)
    if policy is None or policy.broker_id != broker_id:
        raise NotFoundError(f"installment {installment.id} not found")
    return policy


async def initiate_payment(
    db: AsyncSession,
    *,
    actor: PlatformUser,
    installment_id: uuid.UUID,
    broker_id: uuid.UUID,
    squad_client: SquadClient,
    merchant_id: str,
    idempotency_key_id: uuid.UUID | None = None,
) -> Payment:
    """Records a Payment row in 'initiated' status pointing to the broker's
    permanent Static Virtual Account. The caller should display
    squad_virtual_account_number / squad_virtual_account_bank to the
    policyholder so they can transfer the exact amount. commission_config_id
    is resolved and locked here so a later rate change never affects this row.
    """
    installment = await db.get(PremiumInstallment, installment_id)
    if installment is None:
        raise NotFoundError(f"installment {installment_id} not found")
    if installment.status not in (InstallmentStatus.DUE.value, InstallmentStatus.OVERDUE.value):
        raise ConflictError(
            f"installment {installment_id} is not payable (status={installment.status})"
        )
    policy = await load_owned_installment_policy(db, installment, broker_id=broker_id)
    insurance_company_id = policy.insurance_company_id

    in_flight = await db.scalar(
        select(Payment).where(
            Payment.installment_id == installment_id,
            Payment.status == PaymentStatus.INITIATED.value,
        )
    )
    if in_flight is not None:
        raise ConflictError(f"installment {installment_id} already has a payment in flight")

    in_flight_batch_item = await db.scalar(
        select(PaymentBatchItem)
        .join(PaymentBatch, PaymentBatchItem.payment_batch_id == PaymentBatch.id)
        .where(
            PaymentBatchItem.installment_id == installment_id,
            PaymentBatch.status == PaymentStatus.INITIATED.value,
        )
    )
    if in_flight_batch_item is not None:
        raise ConflictError(f"installment {installment_id} already has a bulk payment in flight")

    broker = await db.get(Broker, broker_id)
    if broker is None or not broker.squad_va_number:
        raise UnprocessableError(
            f"broker {broker_id} has no virtual account configured; "
            "contact an Insureflow Admin to provision one"
        )

    commission_config = await resolve_commission_config(
        db, broker_id=broker_id, insurance_company_id=insurance_company_id
    )

    transaction_ref = generate_squad_ref(merchant_id)

    payment = Payment(
        installment_id=installment_id,
        broker_id=broker_id,
        insurance_company_id=insurance_company_id,
        initiated_by=actor.id,
        commission_config_id=commission_config.id,
        amount_kobo=installment.amount_kobo,
        status=PaymentStatus.INITIATED.value,
        squad_transaction_ref=transaction_ref,
        squad_virtual_account_number=broker.squad_va_number,
        squad_virtual_account_bank=broker.squad_va_bank,
        va_expires_at=None,
        idempotency_key_id=idempotency_key_id,
    )
    db.add(payment)
    await db.flush()

    await record_audit_log(
        db,
        action="payment.initiated",
        entity_type="payment",
        entity_id=payment.id,
        actor_id=actor.id,
        actor_role=actor.role,
        after_state={
            "amount_kobo": payment.amount_kobo,
            "squad_transaction_ref": transaction_ref,
            "squad_virtual_account_number": broker.squad_va_number,
        },
    )
    await db.flush()
    return payment


async def resolve_payment_outcome(
    db: AsyncSession,
    payment: Payment,
    requery_result: StaticVATransaction,
    *,
    squad_client: SquadClient,
    merchant_id: str,
) -> Payment:
    """The single entry point that flips a Payment out of 'initiated', driven
    only by an independently re-queried transaction_status -- never the raw
    webhook body (CLAUDE.md). Idempotent: a payment already in a terminal
    state is returned unchanged, so a duplicate webhook delivery is a no-op.
    """
    if payment.status in _TERMINAL_STATUSES:
        return payment

    status = requery_result.transaction_status.upper()
    if status == "SUCCESS":
        return await _mark_success(
            db, payment, requery_result, squad_client=squad_client, merchant_id=merchant_id
        )

    payment.status = PaymentStatus.FAILED.value
    payment.failure_reason = f"squad transaction_status={status}"
    payment.raw_squad_response = requery_result.raw
    await record_audit_log(
        db,
        action="payment.failed",
        entity_type="payment",
        entity_id=payment.id,
        after_state={"status": payment.status, "failure_reason": payment.failure_reason},
    )
    await db.flush()
    payment_outcomes_total.labels(status=payment.status).inc()
    _logger.warning(
        "payment.failed", payment_id=str(payment.id), failure_reason=payment.failure_reason
    )
    return payment


async def _mark_success(
    db: AsyncSession,
    payment: Payment,
    requery_result: StaticVATransaction,
    *,
    squad_client: SquadClient,
    merchant_id: str,
) -> Payment:
    payment.status = PaymentStatus.SUCCESS.value
    payment.raw_squad_response = requery_result.raw

    installment = await db.get(PremiumInstallment, payment.installment_id)
    if installment is None:
        raise NotFoundError(f"installment {payment.installment_id} not found")
    installment.status = InstallmentStatus.PAID.value
    installment.payment_id = payment.id

    commission_config = await db.get(CommissionConfig, payment.commission_config_id)
    if commission_config is None:
        raise NotFoundError(f"commission config {payment.commission_config_id} not found")
    split = calculate_split(payment.amount_kobo, commission_config)

    broker_clearing = await get_or_create_ledger_account(
        db, account_type="BROKER_CLEARING", broker_id=payment.broker_id
    )
    gtbank_revenue = await get_or_create_ledger_account(db, account_type="GTBANK_REVENUE")
    insureflow_revenue = await get_or_create_ledger_account(db, account_type="INSUREFLOW_REVENUE")

    postings = [
        LedgerPosting(
            ledger_account_id=broker_clearing.id,
            entry_type="debit",
            amount_kobo=split.gross_amount_kobo,
            reference_type="payment",
            reference_id=payment.id,
        ),
        LedgerPosting(
            ledger_account_id=gtbank_revenue.id,
            entry_type="credit",
            amount_kobo=split.gtbank_kobo,
            reference_type="payment",
            reference_id=payment.id,
        ),
        LedgerPosting(
            ledger_account_id=insureflow_revenue.id,
            entry_type="credit",
            amount_kobo=split.insureflow_kobo,
            reference_type="payment",
            reference_id=payment.id,
        ),
    ]
    if split.broker_kobo > 0:
        broker_commission = await get_or_create_ledger_account(
            db, account_type="BROKER_COMMISSION", broker_id=payment.broker_id
        )
        postings.append(
            LedgerPosting(
                ledger_account_id=broker_commission.id,
                entry_type="credit",
                amount_kobo=split.broker_kobo,
                reference_type="payment",
                reference_id=payment.id,
            )
        )
    if split.insurer_payable_kobo > 0:
        insurer_payable = await get_or_create_ledger_account(
            db, account_type="INSURER_PAYABLE", insurance_company_id=payment.insurance_company_id
        )
        postings.append(
            LedgerPosting(
                ledger_account_id=insurer_payable.id,
                entry_type="credit",
                amount_kobo=split.insurer_payable_kobo,
                reference_type="payment",
                reference_id=payment.id,
            )
        )

    await post_ledger_entries(db, postings)

    await record_audit_log(
        db,
        action="payment.success",
        entity_type="payment",
        entity_id=payment.id,
        after_state={"amount_kobo": payment.amount_kobo},
    )
    await db.flush()
    payment_outcomes_total.labels(status=payment.status).inc()
    _logger.info("payment.success", payment_id=str(payment.id), amount_kobo=payment.amount_kobo)

    if split.insurer_payable_kobo > 0:
        insurance_company = await db.get(InsuranceCompany, payment.insurance_company_id)
        if insurance_company is None:
            raise NotFoundError(f"insurance company {payment.insurance_company_id} not found")
        await settlement_service.settle_payment(
            db,
            insurance_company=insurance_company,
            source_type="payment",
            source_id=payment.id,
            amount_kobo=split.insurer_payable_kobo,
            squad_client=squad_client,
            merchant_id=merchant_id,
        )

    return payment
