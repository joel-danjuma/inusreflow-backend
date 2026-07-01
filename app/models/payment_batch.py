import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import PaymentStatus


class PaymentBatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One bulk-collection attempt covering many installments via a single
    Squad Dynamic Virtual Account for the combined total (PRD §8.3) -- the
    broker is debited once and, on success, the insurer is settled once for
    the whole batch net of commission, regardless of item_count. Mirrors
    Payment's status lifecycle and locked commission_config_id exactly; a
    failed/mismatched/expired attempt is never retried in place -- a fresh
    POST /payments/bulk call creates a brand new PaymentBatch with its own VA.
    """

    __tablename__ = "payment_batches"
    __table_args__ = (
        CheckConstraint(
            "status IN ('initiated', 'success', 'mismatch', 'expired', 'failed')",
            name="ck_payment_batches_status",
        ),
        CheckConstraint("item_count > 0", name="ck_payment_batches_item_count_positive"),
        Index("ix_payment_batches_broker_id_status", "broker_id", "status"),
    )

    broker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brokers.id"), nullable=False
    )
    insurance_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurance_companies.id"), nullable=False
    )
    initiated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("platform_users.id"), nullable=False
    )
    commission_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commission_configs.id"), nullable=False
    )
    idempotency_key_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("idempotency_keys.id"), nullable=True
    )

    total_amount_kobo: Mapped[int] = mapped_column(BigInteger, nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=PaymentStatus.INITIATED.value
    )

    squad_transaction_ref: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    squad_virtual_account_number: Mapped[str | None] = mapped_column(String, nullable=True)
    squad_virtual_account_bank: Mapped[str | None] = mapped_column(String, nullable=True)
    va_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    failure_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_squad_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
