from collections.abc import Mapping
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.metrics import webhook_events_total
from app.integrations.squad.client import SquadClient
from app.integrations.squad.exceptions import SquadAPIError
from app.integrations.squad.signature import verify_static_va_signature
from app.models.broker import Broker
from app.models.enums import PaymentStatus, WebhookProcessingStatus
from app.models.payment import Payment
from app.models.payment_batch import PaymentBatch
from app.models.webhook_event import WebhookEvent
from app.services import bulk_payment_service, payment_service
from app.services.audit_service import record_audit_log

_RESOLVED_STATUSES = frozenset(
    {WebhookProcessingStatus.PROCESSED.value, WebhookProcessingStatus.REJECTED.value}
)

_logger = structlog.get_logger(__name__)


def _header(headers: Mapping[str, str], name: str) -> str:
    lowered = name.lower()
    for key, value in headers.items():
        if key.lower() == lowered:
            return value
    return ""


async def _claim_webhook_event(
    db: AsyncSession,
    *,
    event_type: str,
    transaction_ref: str,
    raw_payload: dict[str, Any],
    raw_headers: dict[str, Any],
    signature_valid: bool,
) -> tuple[WebhookEvent, bool]:
    """INSERT ... ON CONFLICT DO NOTHING on (transaction_ref, event_type) --
    Squad's own retries hit the same row instead of erroring (CLAUDE.md /
    app.models.webhook_event docstring). Returns (row, is_new).
    transaction_ref for SVA webhooks is Squad's own transaction_reference
    (their UUID, unique per bank transfer), not our internal squad_transaction_ref.
    """
    stmt = (
        pg_insert(WebhookEvent)
        .values(
            event_type=event_type,
            transaction_ref=transaction_ref,
            raw_payload=raw_payload,
            raw_headers=raw_headers,
            signature_valid=signature_valid,
            processing_status=WebhookProcessingStatus.PENDING.value,
        )
        .on_conflict_do_nothing(constraint="ux_webhook_events_transaction_ref_event_type")
        .returning(WebhookEvent)
    )
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if row is not None:
        await db.flush()
        return row, True

    existing = await db.scalar(
        select(WebhookEvent).where(
            WebhookEvent.transaction_ref == transaction_ref,
            WebhookEvent.event_type == event_type,
        )
    )
    if existing is None:
        raise RuntimeError("webhook event claim conflicted but no existing row was found")
    return existing, False


async def handle_squad_webhook(
    db: AsyncSession,
    *,
    payload: dict[str, Any],
    headers: Mapping[str, str],
    secret_key: str,
    squad_client: SquadClient,
    merchant_id: str,
) -> WebhookEvent:
    """Handles SVA (Static Virtual Account) webhooks from Squad.

    Persists every delivery verbatim before anything else, verifies
    x-squad-signature (pipe-delimited HMAC-SHA512), then -- only for a
    signature-valid event not already terminally resolved -- correlates the
    incoming transfer to an initiated Payment/PaymentBatch by:
      1. VA number → broker
      2. oldest initiated Payment/Batch for broker with matching amount_kobo

    Squad's own transaction_reference (their UUID) is stored as
    squad_webhook_tx_ref on the Payment/Batch and used for the mandatory
    independent re-query (GET /transaction/verify/{ref}) before any financial
    state change (CLAUDE.md).
    """
    # SVA webhook fields
    squad_tx_ref = str(payload.get("transaction_reference") or "")
    virtual_account_number = str(payload.get("virtual_account_number") or "")
    currency = str(payload.get("currency") or "NGN")
    principal_amount_str = str(payload.get("principal_amount") or "0")
    settled_amount_str = str(payload.get("settled_amount") or "0")
    customer_identifier = str(payload.get("customer_identifier") or "")
    event_type = str(payload.get("transaction_type") or "static_virtual_account")

    signature_valid = verify_static_va_signature(
        secret_key=secret_key,
        header_signature=_header(headers, "x-squad-signature"),
        transaction_reference=squad_tx_ref,
        virtual_account_number=virtual_account_number,
        currency=currency,
        principal_amount=principal_amount_str,
        settled_amount=settled_amount_str,
        customer_identifier=customer_identifier,
    )

    # Dedup key is Squad's own transaction_reference -- unique per actual transfer.
    event, _ = await _claim_webhook_event(
        db,
        event_type=event_type,
        transaction_ref=squad_tx_ref,
        raw_payload=payload,
        raw_headers=dict(headers),
        signature_valid=signature_valid,
    )
    if event.processing_status in _RESOLVED_STATUSES:
        return event

    if not event.signature_valid:
        event.processing_status = WebhookProcessingStatus.REJECTED.value
        event.failure_reason = "invalid signature"
        await record_audit_log(
            db,
            action="webhook_event.rejected",
            entity_type="webhook_event",
            entity_id=event.id,
            after_state={"transaction_ref": event.transaction_ref},
        )
        await db.flush()
        webhook_events_total.labels(
            signature_valid="false", processing_status=event.processing_status
        ).inc()
        _logger.warning(
            "webhook_event.rejected",
            event_id=str(event.id),
            transaction_ref=event.transaction_ref,
        )
        return event

    # Convert principal_amount to kobo for matching.
    # Squad sends principal_amount as an integer (kobo).
    try:
        principal_amount_kobo = int(principal_amount_str)
    except ValueError:
        principal_amount_kobo = 0

    # Find broker by VA number.
    broker = await db.scalar(select(Broker).where(Broker.squad_va_number == virtual_account_number))
    if broker is None:
        event.processing_status = WebhookProcessingStatus.FAILED.value
        event.failure_reason = (
            f"no broker found for virtual_account_number={virtual_account_number!r}"
        )
        await db.flush()
        webhook_events_total.labels(
            signature_valid="true", processing_status=event.processing_status
        ).inc()
        _logger.error(
            "webhook_event.failed",
            event_id=str(event.id),
            failure_reason=event.failure_reason,
        )
        return event

    # Find oldest initiated Payment for this broker with matching amount (FIFO).
    payment = await db.scalar(
        select(Payment)
        .where(
            Payment.broker_id == broker.id,
            Payment.squad_virtual_account_number == virtual_account_number,
            Payment.amount_kobo == principal_amount_kobo,
            Payment.status == PaymentStatus.INITIATED.value,
        )
        .order_by(Payment.created_at.asc())
        .limit(1)
    )

    batch: PaymentBatch | None = None
    if payment is None:
        batch = await db.scalar(
            select(PaymentBatch)
            .where(
                PaymentBatch.broker_id == broker.id,
                PaymentBatch.squad_virtual_account_number == virtual_account_number,
                PaymentBatch.total_amount_kobo == principal_amount_kobo,
                PaymentBatch.status == PaymentStatus.INITIATED.value,
            )
            .order_by(PaymentBatch.created_at.asc())
            .limit(1)
        )

    if payment is None and batch is None:
        event.processing_status = WebhookProcessingStatus.FAILED.value
        event.failure_reason = (
            f"no initiated payment or batch found for broker={broker.id} "
            f"amount_kobo={principal_amount_kobo}"
        )
        await db.flush()
        webhook_events_total.labels(
            signature_valid="true", processing_status=event.processing_status
        ).inc()
        _logger.error(
            "webhook_event.failed",
            event_id=str(event.id),
            failure_reason=event.failure_reason,
        )
        return event

    # Store Squad's tx ref for audit / future re-query.
    if payment is not None:
        payment.squad_webhook_tx_ref = squad_tx_ref
    else:
        assert batch is not None
        batch.squad_webhook_tx_ref = squad_tx_ref
    await db.flush()

    # Independent re-query before any financial state change (CLAUDE.md).
    try:
        requery_result = await squad_client.verify_transaction(squad_tx_ref)
    except SquadAPIError as exc:
        event.processing_status = WebhookProcessingStatus.FAILED.value
        event.failure_reason = f"squad re-query failed: {exc}"
        await db.flush()
        webhook_events_total.labels(
            signature_valid="true", processing_status=event.processing_status
        ).inc()
        _logger.error(
            "webhook_event.failed",
            event_id=str(event.id),
            failure_reason=event.failure_reason,
        )
        return event

    if requery_result is None:
        event.processing_status = WebhookProcessingStatus.FAILED.value
        event.failure_reason = "squad re-query returned no transaction"
        await db.flush()
        webhook_events_total.labels(
            signature_valid="true", processing_status=event.processing_status
        ).inc()
        _logger.error(
            "webhook_event.failed",
            event_id=str(event.id),
            failure_reason=event.failure_reason,
        )
        return event

    if payment is not None:
        await payment_service.resolve_payment_outcome(
            db, payment, requery_result, squad_client=squad_client, merchant_id=merchant_id
        )
        resource_state: dict[str, Any] = {"payment_id": str(payment.id)}
    elif batch is not None:
        await bulk_payment_service.resolve_batch_outcome(
            db, batch, requery_result, squad_client=squad_client, merchant_id=merchant_id
        )
        resource_state = {"payment_batch_id": str(batch.id)}
    else:
        raise RuntimeError("unreachable: payment and batch both None after existence check")

    event.processing_status = WebhookProcessingStatus.PROCESSED.value
    await record_audit_log(
        db,
        action="webhook_event.processed",
        entity_type="webhook_event",
        entity_id=event.id,
        after_state={"transaction_ref": event.transaction_ref, **resource_state},
    )
    await db.flush()
    webhook_events_total.labels(
        signature_valid="true", processing_status=event.processing_status
    ).inc()
    return event
