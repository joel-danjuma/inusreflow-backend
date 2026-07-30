import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import OnboardingStatus


class Broker(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Deliberately has no insurance_company_id FK — see BrokerInsurerAssignment,
    which models the relationship as many-to-many-ready even though it's 1:1 today.
    """

    __tablename__ = "brokers"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'suspended')",
            name="ck_brokers_status",
        ),
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    contact_email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=OnboardingStatus.PENDING.value
    )
    rejection_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    kyb_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # KYB fields required for Business SVA creation at approval time
    bvn: Mapped[str | None] = mapped_column(String(11), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Permanent Business SVA assigned at broker approval (one per broker, never recreated
    # per payment -- see docs/adr and plan for SVA correlation rationale).
    squad_va_number: Mapped[str | None] = mapped_column(String, nullable=True)
    squad_va_bank: Mapped[str | None] = mapped_column(String, nullable=True)
    squad_customer_identifier: Mapped[str | None] = mapped_column(String, nullable=True)
