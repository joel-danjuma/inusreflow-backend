import uuid
from datetime import date

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import InstallmentStatus


class PremiumInstallment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One due date for a policy's recurring premium. Never auto-debited — a
    broker must explicitly trigger payment (see CLAUDE.md); a scheduled job
    only flags overdue, it never charges.

    payment_id is set only once a single Payment resolves to 'success';
    payment_batch_item_id is set only once the PaymentBatchItem's batch
    resolves to 'success' (a bulk collection, PRD §8.3) — never both, and
    never on 'initiated'/'mismatch'/'expired'/'failed'.
    """

    __tablename__ = "premium_installments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('due', 'overdue', 'paid', 'cancelled')",
            name="ck_premium_installments_status",
        ),
        CheckConstraint(
            "NOT (payment_id IS NOT NULL AND payment_batch_item_id IS NOT NULL)",
            name="ck_premium_installments_payment_xor_batch_item",
        ),
        UniqueConstraint("policy_id", "due_date", name="ux_premium_installments_policy_due_date"),
        Index("ix_premium_installments_status_due_date", "status", "due_date"),
    )

    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("policies.id"), nullable=False
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount_kobo: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default=InstallmentStatus.DUE.value)
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payments.id"), nullable=True
    )
    payment_batch_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_batch_items.id"), nullable=True
    )
