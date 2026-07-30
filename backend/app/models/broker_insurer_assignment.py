import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BrokerInsurerAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The broker-insurer relationship is genuinely many-to-many: a broker can
    have several simultaneously-active insurer assignments and vice versa.
    The partial unique index below enforces only that a given (broker,
    insurer) *pair* can't be double-active -- it does not limit a broker (or
    insurer) to a single counterparty. Reassigning/unassigning one pair never
    touches the broker's other active assignments.
    """

    __tablename__ = "broker_insurer_assignments"
    __table_args__ = (
        Index(
            "ux_broker_insurer_assignments_active_pair",
            "broker_id",
            "insurance_company_id",
            unique=True,
            postgresql_where=text("is_active"),
        ),
    )

    broker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brokers.id"), nullable=False
    )
    insurance_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurance_companies.id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
