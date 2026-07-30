from typing import Any

from sqlalchemy import Boolean, CheckConstraint, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import WebhookProcessingStatus


class WebhookEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Every Squad webhook delivery is persisted here verbatim -- raw body and
    headers -- before anything else happens, signature-valid or not
    (CLAUDE.md). event_type is Squad's transaction_type field (e.g.
    "dynamic_virtual_account"); (transaction_ref, event_type) is the
    idempotent-processing dedup key from PRD §8.5. A unique-violation on
    insert means this exact delivery was already recorded -- the service
    layer falls back to the existing row rather than failing the webhook
    call, so Squad's own retries are harmless.
    """

    __tablename__ = "webhook_events"
    __table_args__ = (
        CheckConstraint(
            "processing_status IN ('pending', 'processed', 'rejected', 'failed')",
            name="ck_webhook_events_processing_status",
        ),
        UniqueConstraint(
            "transaction_ref", "event_type", name="ux_webhook_events_transaction_ref_event_type"
        ),
    )

    event_type: Mapped[str] = mapped_column(String, nullable=False)
    transaction_ref: Mapped[str] = mapped_column(String, nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    raw_headers: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    signature_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    processing_status: Mapped[str] = mapped_column(
        String, nullable=False, default=WebhookProcessingStatus.PENDING.value
    )
    failure_reason: Mapped[str | None] = mapped_column(String, nullable=True)
