from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.squad.client import SquadClient
from app.models.enums import PaymentStatus, SettlementPayoutStatus
from app.models.payment import Payment
from app.models.payment_batch import PaymentBatch
from app.models.settlement_payout import SettlementPayout
from app.services import bulk_payment_service, payment_service
from app.services.audit_service import record_audit_log


@dataclass(frozen=True)
class TransactionReconciliationResult:
    payments_checked: int
    payments_resolved: int
    batches_checked: int
    batches_resolved: int


@dataclass(frozen=True)
class TransferReconciliationResult:
    payouts_checked: int
    payouts_resolved: int
    mismatches_flagged: int


async def reconcile_transactions(
    db: AsyncSession,
    *,
    squad_client: SquadClient,
    merchant_id: str,
    stale_after: timedelta,
) -> TransactionReconciliationResult:
    """Catches missed/out-of-order webhooks (PRD §8.5): every Payment/
    PaymentBatch still 'initiated' longer than stale_after is independently
    re-queried against Squad and resolved through the exact same entry
    points the webhook path uses (payment_service.resolve_payment_outcome /
    bulk_payment_service.resolve_batch_outcome) -- never a separate write
    path, so a transaction resolved by reconciliation is indistinguishable
    from one resolved by a normal webhook delivery.
    """
    cutoff = datetime.now(UTC) - stale_after

    stale_payments = (
        await db.scalars(
            select(Payment).where(
                Payment.status == PaymentStatus.INITIATED.value,
                Payment.created_at < cutoff,
            )
        )
    ).all()
    payments_resolved = 0
    for payment in stale_payments:
        # SVA payments (va_expires_at IS NULL): Squad's tx_ref is only known after
        # a webhook arrives. If still None, Squad hasn't fired the webhook yet --
        # skip and rely on Squad's 24 h retry policy. After the extended stale
        # window the payment will be marked failed on the next reconciliation run.
        if payment.squad_webhook_tx_ref is None:
            continue
        requery_result = await squad_client.verify_transaction(payment.squad_webhook_tx_ref)
        if requery_result is None:
            continue
        await payment_service.resolve_payment_outcome(
            db, payment, requery_result, squad_client=squad_client, merchant_id=merchant_id
        )
        if payment.status != PaymentStatus.INITIATED.value:
            payments_resolved += 1

    stale_batches = (
        await db.scalars(
            select(PaymentBatch).where(
                PaymentBatch.status == PaymentStatus.INITIATED.value,
                PaymentBatch.created_at < cutoff,
            )
        )
    ).all()
    batches_resolved = 0
    for batch in stale_batches:
        if batch.squad_webhook_tx_ref is None:
            continue
        requery_result = await squad_client.verify_transaction(batch.squad_webhook_tx_ref)
        if requery_result is None:
            continue
        await bulk_payment_service.resolve_batch_outcome(
            db, batch, requery_result, squad_client=squad_client, merchant_id=merchant_id
        )
        if batch.status != PaymentStatus.INITIATED.value:
            batches_resolved += 1

    return TransactionReconciliationResult(
        payments_checked=len(stale_payments),
        payments_resolved=payments_resolved,
        batches_checked=len(stale_batches),
        batches_resolved=batches_resolved,
    )


async def reconcile_transfers(
    db: AsyncSession,
    *,
    squad_client: SquadClient,
    page_size: int = 50,
) -> TransferReconciliationResult:
    """Cross-checks settlement_payouts against Squad's authoritative
    GET /payout/list (PRD §8.5/§15). A PENDING payout -- settle_payment now
    resolves most attempts to a terminal status immediately via
    requery_transfer, but a still-ambiguous response is left PENDING -- is
    resolved here to Squad's reported terminal status. A payout already
    recorded as a terminal status that now disagrees with Squad's listing
    (e.g. a bank-side reversal surfacing after the fact) is never silently
    rewritten -- only audit-logged for human review, since correcting an
    already-posted ledger entry is a bigger feature this phase doesn't build
    (see docs/adr/0005-reconciliation-scope.md).
    """
    remote_status_by_ref: dict[str, str] = {}
    page = 1
    while True:
        items = await squad_client.list_transfers(page=page, per_page=page_size)
        if not items:
            break
        for item in items:
            remote_status_by_ref[item.transaction_reference] = item.transaction_status
        page += 1

    if not remote_status_by_ref:
        return TransferReconciliationResult(
            payouts_checked=0, payouts_resolved=0, mismatches_flagged=0
        )

    payouts = (
        await db.scalars(
            select(SettlementPayout).where(
                SettlementPayout.squad_transfer_ref.in_(remote_status_by_ref.keys())
            )
        )
    ).all()

    payouts_resolved = 0
    mismatches_flagged = 0
    for payout in payouts:
        remote_status = remote_status_by_ref[payout.squad_transfer_ref]
        if payout.status == SettlementPayoutStatus.PENDING.value:
            payout.status = (
                SettlementPayoutStatus.SUCCESS.value
                if remote_status == "success"
                else SettlementPayoutStatus.FAILED.value
            )
            if payout.status == SettlementPayoutStatus.FAILED.value:
                payout.failure_reason = (
                    f"resolved by reconciliation: squad transaction_status={remote_status}"
                )
            await record_audit_log(
                db,
                action="settlement_payout.reconciled",
                entity_type="settlement_payout",
                entity_id=payout.id,
                before_state={"status": "pending"},
                after_state={"status": payout.status, "squad_transaction_status": remote_status},
            )
            payouts_resolved += 1
        elif payout.status != remote_status:
            await record_audit_log(
                db,
                action="settlement_payout.reconciliation_mismatch",
                entity_type="settlement_payout",
                entity_id=payout.id,
                before_state={"local_status": payout.status},
                after_state={"squad_transaction_status": remote_status},
            )
            mismatches_flagged += 1

    await db.flush()
    return TransferReconciliationResult(
        payouts_checked=len(payouts),
        payouts_resolved=payouts_resolved,
        mismatches_flagged=mismatches_flagged,
    )
