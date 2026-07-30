import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ReminderChannel, ReminderStatus


class Reminder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Insurer -> broker nudge about a specific overdue-able installment.
    broker_id is denormalized from the installment's policy for fast
    broker-scoped lookup.

    There's no real email infrastructure yet (same gap onboarding's
    activation-token-returned-in-response workaround papers over), so
    "sending" is simulated by flipping status/sent_at, not a real dispatch.
    """

    __tablename__ = "reminders"
    __table_args__ = (
        CheckConstraint("channel IN ('email')", name="ck_reminders_channel"),
        CheckConstraint("status IN ('queued', 'sent', 'failed')", name="ck_reminders_status"),
    )

    installment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("premium_installments.id"), nullable=False
    )
    broker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brokers.id"), nullable=False
    )
    sent_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("platform_users.id"), nullable=False
    )
    channel: Mapped[str] = mapped_column(
        String, nullable=False, default=ReminderChannel.EMAIL.value
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default=ReminderStatus.QUEUED.value)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
