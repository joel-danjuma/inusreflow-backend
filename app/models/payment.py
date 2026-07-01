import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import PaymentStatus


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One single-premium collection attempt via a Squad Dynamic Virtual
    Account (docs/adr/0004-squad-virtual-account-collection.md) -- there is
    no card/bank charge reference here, only a VA the payer transfers into.
    commission_config_id is resolved and locked at creation time, before any
    Squad call, so a later rate change can never retroactively alter this
    row (CLAUDE.md). A failed/mismatched/expired attempt is never retried in
    place -- a fresh POST /payments call creates a brand new Payment row
    with its own VA and squad_transaction_ref.
    """

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('initiated', 'success', 'mismatch', 'expired', 'failed')",
            name="ck_payments_status",
        ),
        Index("ix_payments_installment_id_status", "installment_id", "status"),
    )

    installment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("premium_installments.id"), nullable=False
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

    amount_kobo: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=PaymentStatus.INITIATED.value
    )

    squad_transaction_ref: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    squad_virtual_account_number: Mapped[str | None] = mapped_column(String, nullable=True)
    squad_virtual_account_bank: Mapped[str | None] = mapped_column(String, nullable=True)
    va_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    failure_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_squad_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
