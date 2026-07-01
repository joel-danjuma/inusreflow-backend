import uuid
from collections.abc import Sequence

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, UnprocessableError
from app.core.metrics import payment_batch_outcomes_total
from app.integrations.squad.client import SquadClient, generate_squad_ref
from app.integrations.squad.schemas import DynamicVirtualAccountTransaction
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
from app.services.anomaly_service import flag_if_anomalous_batch
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


async def _load_payable_installments(
    db: AsyncSession,
    installment_ids: Sequence[uuid.UUID],
    *,
    broker_id: uuid.UUID,
    insurance_company_id: uuid.UUID,
) -> list[PremiumInstallment]:
    """Validates every installment up front -- exists, payable, owned by this
    broker/insurer -- before any Squad call, so one bad id fails the whole
    request rather than partially collecting (CLAUDE.md: "one debit, one
    settlement"). Batch-fetches installments and their policies in two
    queries instead of one round trip per id via payment_service.
    assert_installment_owned_by -- a Locust run at the 500-item cap
    (tests/load/, docs/adr/0008-load-testing.md) measured the original
    per-id db.get() loop alone at ~8s, dominating request latency.
    """
    installments_by_id = {
        installment.id: installment
        for installment in (
            await db.scalars(
                select(PremiumInstallment).where(PremiumInstallment.id.in_(installment_ids))
            )
        ).all()
    }

    missing_id = next((iid for iid in installment_ids if iid not in installments_by_id), None)
    if missing_id is not None:
        raise NotFoundError(f"installment {missing_id} not found")

    policy_ids = {installment.policy_id for installment in installments_by_id.values()}
    policies_by_id = {
        policy.id: policy
        for policy in (await db.scalars(select(Policy).where(Policy.id.in_(policy_ids)))).all()
    }

    installments: list[PremiumInstallment] = []
    for installment_id in installment_ids:
        installment = installments_by_id[installment_id]
        if installment.status not in (InstallmentStatus.DUE.value, InstallmentStatus.OVERDUE.value):
            raise ConflictError(
                f"installment {installment_id} is not payable (status={installment.status})"
            )
        policy = policies_by_id.get(installment.policy_id)
        if (
            policy is None
            or policy.broker_id != broker_id
            or policy.insurance_company_id != insurance_company_id
        ):
            raise NotFoundError(f"installment {installment_id} not found")
        installments.append(installment)
    return installments


async def _assert_no_in_flight_claim(
    db: AsyncSession, installment_ids: Sequence[uuid.UUID]
) -> None:
    """Symmetric counterpart to payment_service's in-flight check -- an
    installment already claimed by an in-flight single Payment, or by another
    in-flight PaymentBatchItem, can't be claimed again by this batch.
    """
    in_flight_payment = await db.scalar(
        select(Payment).where(
            Payment.installment_id.in_(installment_ids),
            Payment.status == PaymentStatus.INITIATED.value,
        )
    )
    if in_flight_payment is not None:
        raise ConflictError(
            f"installment {in_flight_payment.installment_id} already has a payment in flight"
        )

    in_flight_item = await db.scalar(
        select(PaymentBatchItem)
        .join(PaymentBatch, PaymentBatchItem.payment_batch_id == PaymentBatch.id)
        .where(
            PaymentBatchItem.installment_id.in_(installment_ids),
            PaymentBatch.status == PaymentStatus.INITIATED.value,
        )
    )
    if in_flight_item is not None:
        raise ConflictError(
            f"installment {in_flight_item.installment_id} already has a bulk payment in flight"
        )


async def initiate_bulk_payment(
    db: AsyncSession,
    *,
    actor: PlatformUser,
    installment_ids: Sequence[uuid.UUID],
    broker_id: uuid.UUID,
    insurance_company_id: uuid.UUID,
    squad_client: SquadClient,
    merchant_id: str,
    duration_seconds: int,
    max_items: int,
    idempotency_key_id: uuid.UUID | None = None,
) -> PaymentBatch:
    """Mints one Squad Dynamic Virtual Account for the combined total of every
    installment and records a PaymentBatch + one PaymentBatchItem per
    installment, all in 'initiated' status (PRD §8.3) -- the broker is
    debited once for the whole batch, never once per item. commission_config
    is resolved and locked here, before any Squad call, exactly as for a
    single payment.
    """
    if not installment_ids:
        raise UnprocessableError("installment_ids must not be empty")
    if len(installment_ids) > max_items:
        raise UnprocessableError(
            f"batch of {len(installment_ids)} items exceeds the cap of {max_items}"
        )
    if len(set(installment_ids)) != len(installment_ids):
        raise UnprocessableError("installment_ids must not contain duplicates")

    installments = await _load_payable_installments(
        db, installment_ids, broker_id=broker_id, insurance_company_id=insurance_company_id
    )
    await _assert_no_in_flight_claim(db, installment_ids)

    total_amount_kobo = sum(installment.amount_kobo for installment in installments)
    commission_config = await resolve_commission_config(
        db, broker_id=broker_id, insurance_company_id=insurance_company_id
    )

    transaction_ref = generate_squad_ref(merchant_id)
    va = await squad_client.create_dynamic_virtual_account(
        amount_kobo=total_amount_kobo,
        duration_seconds=duration_seconds,
        email=actor.email,
        transaction_ref=transaction_ref,
    )

    batch = PaymentBatch(
        broker_id=broker_id,
        insurance_company_id=insurance_company_id,
        initiated_by=actor.id,
        commission_config_id=commission_config.id,
        total_amount_kobo=total_amount_kobo,
        item_count=len(installments),
        status=PaymentStatus.INITIATED.value,
        squad_transaction_ref=transaction_ref,
        squad_virtual_account_number=va.account_number,
        squad_virtual_account_bank=va.bank,
        va_expires_at=va.expires_at,
        raw_squad_response=va.raw,
        idempotency_key_id=idempotency_key_id,
    )
    db.add(batch)
    await db.flush()

    for installment in installments:
        db.add(
            PaymentBatchItem(
                payment_batch_id=batch.id,
                installment_id=installment.id,
                amount_kobo=installment.amount_kobo,
            )
        )
    await db.flush()

    await record_audit_log(
        db,
        action="payment_batch.initiated",
        entity_type="payment_batch",
        entity_id=batch.id,
        actor_id=actor.id,
        actor_role=actor.role,
        after_state={
            "total_amount_kobo": batch.total_amount_kobo,
            "item_count": batch.item_count,
            "squad_transaction_ref": transaction_ref,
        },
    )
    await db.flush()

    await flag_if_anomalous_batch(db, batch)
    return batch


async def resolve_batch_outcome(
    db: AsyncSession,
    batch: PaymentBatch,
    requery_result: DynamicVirtualAccountTransaction,
    *,
    squad_client: SquadClient,
    merchant_id: str,
) -> PaymentBatch:
    """Mirrors payment_service.resolve_payment_outcome -- the single entry
    point that flips a PaymentBatch out of 'initiated', driven only by an
    independently re-queried transaction_status. Idempotent: a batch already
    in a terminal state is returned unchanged.
    """
    if batch.status in _TERMINAL_STATUSES:
        return batch

    status = requery_result.transaction_status
    if status == "SUCCESS":
        return await _mark_batch_success(
            db, batch, requery_result, squad_client=squad_client, merchant_id=merchant_id
        )
    if status in ("MISMATCH", "EXPIRED"):
        batch.status = status.lower()
        batch.failure_reason = f"squad transaction_status={status}"
        batch.raw_squad_response = requery_result.raw
        await record_audit_log(
            db,
            action="payment_batch.failed",
            entity_type="payment_batch",
            entity_id=batch.id,
            after_state={"status": batch.status, "failure_reason": batch.failure_reason},
        )
        await db.flush()
        payment_batch_outcomes_total.labels(status=batch.status).inc()
        _logger.warning(
            "payment_batch.failed", batch_id=str(batch.id), failure_reason=batch.failure_reason
        )
        return batch

    batch.status = PaymentStatus.FAILED.value
    batch.failure_reason = f"unrecognized squad transaction_status: {status!r}"
    batch.raw_squad_response = requery_result.raw
    await record_audit_log(
        db,
        action="payment_batch.failed",
        entity_type="payment_batch",
        entity_id=batch.id,
        after_state={"status": batch.status, "failure_reason": batch.failure_reason},
    )
    await db.flush()
    payment_batch_outcomes_total.labels(status=batch.status).inc()
    _logger.error(
        "payment_batch.failed", batch_id=str(batch.id), failure_reason=batch.failure_reason
    )
    return batch


async def _mark_batch_success(
    db: AsyncSession,
    batch: PaymentBatch,
    requery_result: DynamicVirtualAccountTransaction,
    *,
    squad_client: SquadClient,
    merchant_id: str,
) -> PaymentBatch:
    batch.status = PaymentStatus.SUCCESS.value
    batch.raw_squad_response = requery_result.raw

    commission_config = await db.get(CommissionConfig, batch.commission_config_id)
    if commission_config is None:
        raise NotFoundError(f"commission config {batch.commission_config_id} not found")

    items = (
        await db.scalars(
            select(PaymentBatchItem).where(PaymentBatchItem.payment_batch_id == batch.id)
        )
    ).all()

    broker_clearing = await get_or_create_ledger_account(
        db, account_type="BROKER_CLEARING", broker_id=batch.broker_id
    )
    gtbank_revenue = await get_or_create_ledger_account(db, account_type="GTBANK_REVENUE")
    insureflow_revenue = await get_or_create_ledger_account(db, account_type="INSUREFLOW_REVENUE")

    total_insurer_payable_kobo = 0
    for item in items:
        installment = await db.get(PremiumInstallment, item.installment_id)
        if installment is None:
            raise NotFoundError(f"installment {item.installment_id} not found")
        installment.status = InstallmentStatus.PAID.value
        installment.payment_batch_item_id = item.id

        split = calculate_split(item.amount_kobo, commission_config)

        postings = [
            LedgerPosting(
                ledger_account_id=broker_clearing.id,
                entry_type="debit",
                amount_kobo=split.gross_amount_kobo,
                reference_type="payment_batch_item",
                reference_id=item.id,
            ),
            LedgerPosting(
                ledger_account_id=gtbank_revenue.id,
                entry_type="credit",
                amount_kobo=split.gtbank_kobo,
                reference_type="payment_batch_item",
                reference_id=item.id,
            ),
            LedgerPosting(
                ledger_account_id=insureflow_revenue.id,
                entry_type="credit",
                amount_kobo=split.insureflow_kobo,
                reference_type="payment_batch_item",
                reference_id=item.id,
            ),
        ]
        if split.broker_kobo > 0:
            broker_commission = await get_or_create_ledger_account(
                db, account_type="BROKER_COMMISSION", broker_id=batch.broker_id
            )
            postings.append(
                LedgerPosting(
                    ledger_account_id=broker_commission.id,
                    entry_type="credit",
                    amount_kobo=split.broker_kobo,
                    reference_type="payment_batch_item",
                    reference_id=item.id,
                )
            )
        if split.insurer_payable_kobo > 0:
            insurer_payable = await get_or_create_ledger_account(
                db,
                account_type="INSURER_PAYABLE",
                insurance_company_id=batch.insurance_company_id,
            )
            postings.append(
                LedgerPosting(
                    ledger_account_id=insurer_payable.id,
                    entry_type="credit",
                    amount_kobo=split.insurer_payable_kobo,
                    reference_type="payment_batch_item",
                    reference_id=item.id,
                )
            )

        # one posting_group_id per item, not per batch (CLAUDE.md) -- keeps
        # per-policy traceability even though collection was one Squad charge.
        await post_ledger_entries(db, postings)
        total_insurer_payable_kobo += split.insurer_payable_kobo

    await record_audit_log(
        db,
        action="payment_batch.success",
        entity_type="payment_batch",
        entity_id=batch.id,
        after_state={"total_amount_kobo": batch.total_amount_kobo, "item_count": batch.item_count},
    )
    await db.flush()
    payment_batch_outcomes_total.labels(status=batch.status).inc()
    _logger.info(
        "payment_batch.success",
        batch_id=str(batch.id),
        total_amount_kobo=batch.total_amount_kobo,
        item_count=batch.item_count,
    )

    if total_insurer_payable_kobo > 0:
        insurance_company = await db.get(InsuranceCompany, batch.insurance_company_id)
        if insurance_company is None:
            raise NotFoundError(f"insurance company {batch.insurance_company_id} not found")
        await settlement_service.settle_payment(
            db,
            insurance_company=insurance_company,
            source_type="payment_batch",
            source_id=batch.id,
            amount_kobo=total_insurer_payable_kobo,
            squad_client=squad_client,
            merchant_id=merchant_id,
        )

    return batch
