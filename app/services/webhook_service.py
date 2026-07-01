from collections.abc import Mapping
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.metrics import webhook_events_total
from app.integrations.squad.client import SquadClient
from app.integrations.squad.exceptions import SquadAPIError
from app.integrations.squad.signature import verify_dynamic_va_signature
from app.models.enums import WebhookProcessingStatus
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
    """Persists every delivery verbatim before anything else, verifies
    x-squad-encrypted-body, and -- only for a signature-valid event not
    already terminally resolved -- independently re-queries the transaction
    before letting payment_service.resolve_payment_outcome touch any
    financial state (CLAUDE.md, docs/adr/0004). A PENDING/FAILED row from an
    earlier delivery is retried rather than short-circuited, so Squad's own
    webhook retry policy doubles as recovery from a transient re-query
    failure; PROCESSED/REJECTED rows are truly terminal and are returned
    as-is.
    """
    transaction_ref = str(payload.get("transaction_reference") or "")
    merchant_reference = str(payload.get("merchant_reference") or "")
    amount_received = str(payload.get("amount_received") or "")
    event_type = str(payload.get("transaction_type") or "dynamic_virtual_account")

    signature_valid = verify_dynamic_va_signature(
        secret_key=secret_key,
        header_signature=_header(headers, "x-squad-encrypted-body"),
        transaction_reference=transaction_ref,
        amount_received=amount_received,
        merchant_reference=merchant_reference,
    )

    event, _ = await _claim_webhook_event(
        db,
        event_type=event_type,
        transaction_ref=transaction_ref,
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

    payment = await db.scalar(
        select(Payment).where(Payment.squad_transaction_ref == event.transaction_ref)
    )
    batch: PaymentBatch | None = None
    if payment is None:
        batch = await db.scalar(
            select(PaymentBatch).where(PaymentBatch.squad_transaction_ref == event.transaction_ref)
        )
    if payment is None and batch is None:
        event.processing_status = WebhookProcessingStatus.FAILED.value
        event.failure_reason = "no matching payment or payment_batch found for this transaction_ref"
        await db.flush()
        webhook_events_total.labels(
            signature_valid="true", processing_status=event.processing_status
        ).inc()
        _logger.error(
            "webhook_event.failed",
            event_id=str(event.id),
            transaction_ref=event.transaction_ref,
            failure_reason=event.failure_reason,
        )
        return event

    try:
        requery_result = await squad_client.get_dynamic_virtual_account_transaction(
            event.transaction_ref
        )
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
            transaction_ref=event.transaction_ref,
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
            transaction_ref=event.transaction_ref,
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
    return event
