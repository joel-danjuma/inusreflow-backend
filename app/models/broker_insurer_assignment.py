import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BrokerInsurerAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The broker-insurer relationship is 1:1 today but modeled many-to-many-ready:
    going many-to-many later means dropping the partial unique index below, not
    migrating brokers/policies/payments.
    """

    __tablename__ = "broker_insurer_assignments"
    __table_args__ = (
        Index(
            "ux_broker_insurer_assignments_active_broker",
            "broker_id",
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
