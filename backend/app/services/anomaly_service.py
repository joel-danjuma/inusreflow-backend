import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.metrics import anomaly_flags_total
from app.models.payment_batch import PaymentBatch
from app.services.audit_service import record_audit_log

_logger = structlog.get_logger(__name__)


async def flag_if_anomalous_batch(db: AsyncSession, batch: PaymentBatch) -> None:
    """Compares a freshly-initiated bulk batch against the broker's own
    trailing history and audit-logs -- never blocks or rejects -- if it's a
    multiplier-sized outlier in item count or total value (PRD §11.5). A
    broker with fewer than Settings.anomaly_min_history_batches prior
    batches has no real baseline yet, so nothing is flagged; this is about
    catching a sudden departure from one broker's own normal, not enforcing
    a platform-wide threshold.
    """
    settings = get_settings()

    history_count, avg_item_count, avg_amount_kobo = (
        await db.execute(
            select(
                func.count(PaymentBatch.id),
                func.avg(PaymentBatch.item_count),
                func.avg(PaymentBatch.total_amount_kobo),
            ).where(PaymentBatch.broker_id == batch.broker_id, PaymentBatch.id != batch.id)
        )
    ).one()

    if history_count < settings.anomaly_min_history_batches:
        return

    reasons = []
    if batch.item_count > float(avg_item_count) * settings.anomaly_batch_item_count_multiplier:
        reasons.append(
            f"item_count {batch.item_count} exceeds "
            f"{settings.anomaly_batch_item_count_multiplier}x the broker's trailing "
            f"average of {float(avg_item_count):.1f} ({history_count} prior batches)"
        )
    if batch.total_amount_kobo > float(avg_amount_kobo) * settings.anomaly_batch_amount_multiplier:
        reasons.append(
            f"total_amount_kobo {batch.total_amount_kobo} exceeds "
            f"{settings.anomaly_batch_amount_multiplier}x the broker's trailing "
            f"average of {float(avg_amount_kobo):.0f} ({history_count} prior batches)"
        )

    if not reasons:
        return

    await record_audit_log(
        db,
        action="payment_batch.anomaly_flagged",
        entity_type="payment_batch",
        entity_id=batch.id,
        actor_id=batch.initiated_by,
        after_state={
            "reasons": reasons,
            "item_count": batch.item_count,
            "total_amount_kobo": batch.total_amount_kobo,
        },
    )
    anomaly_flags_total.inc()
    _logger.warning("payment_batch.anomaly_flagged", batch_id=str(batch.id), reasons=reasons)
