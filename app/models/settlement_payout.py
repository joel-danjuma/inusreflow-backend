import uuid
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import SettlementPayoutStatus


class SettlementPayout(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One Squad Transfer API payout of net-of-commission funds to an
    insurer, fired in real time right after a successful Payment or
    PaymentBatch (PRD §8.6, docs/adr/0003-settlement-mode.md). source_type/
    source_id mirrors LedgerEntry's polymorphic reference -- 'payment' for a
    single payment, 'payment_batch' for one settlement covering an entire
    bulk batch (never one payout per batch item). A failed transfer is never
    retried with the same squad_transfer_ref -- previous_attempt_id chains a
    fresh attempt back to what it's retrying (CLAUDE.md).
    """

    __tablename__ = "settlement_payouts"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('payment', 'payment_batch')",
            name="ck_settlement_payouts_source_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'success', 'failed')", name="ck_settlement_payouts_status"
        ),
        Index("ix_settlement_payouts_source", "source_type", "source_id"),
    )

    insurance_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurance_companies.id"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    amount_kobo: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=SettlementPayoutStatus.PENDING.value
    )
    squad_transfer_ref: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    previous_attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("settlement_payouts.id"), nullable=True
    )
    failure_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_squad_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
