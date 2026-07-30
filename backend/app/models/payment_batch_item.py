import uuid

from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PaymentBatchItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Links one PremiumInstallment to the PaymentBatch that collected it.
    amount_kobo snapshots the installment's amount at batch-creation time, so
    the per-item ledger posting (one posting_group_id per item, not per
    batch -- CLAUDE.md) never depends on the installment row after the fact.
    """

    __tablename__ = "payment_batch_items"
    __table_args__ = (
        UniqueConstraint(
            "payment_batch_id", "installment_id", name="ux_payment_batch_items_batch_installment"
        ),
    )

    payment_batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_batches.id"), nullable=False
    )
    installment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("premium_installments.id"), nullable=False
    )
    amount_kobo: Mapped[int] = mapped_column(BigInteger, nullable=False)
