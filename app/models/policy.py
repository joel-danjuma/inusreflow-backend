import uuid
from datetime import date

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import PolicyStatus

DEFAULT_POLICY_TYPE = "GENERIC"


class Policy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """policy_type is an open string seeded 'GENERIC', never a fixed enum, per
    CLAUDE.md. broker_id/insurance_company_id are denormalized from the owning
    policyholder for fast tenant/broker-scoped queries.
    """

    __tablename__ = "policies"
    __table_args__ = (
        CheckConstraint(
            "premium_frequency IN ('monthly', 'quarterly', 'annually')",
            name="ck_policies_premium_frequency",
        ),
        CheckConstraint(
            "status IN ('active', 'lapsed', 'cancelled')",
            name="ck_policies_status",
        ),
    )

    policyholder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("policyholders.id"), nullable=False
    )
    broker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brokers.id"), nullable=False
    )
    insurance_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurance_companies.id"), nullable=False
    )
    policy_type: Mapped[str] = mapped_column(String, nullable=False, default=DEFAULT_POLICY_TYPE)
    premium_amount_kobo: Mapped[int] = mapped_column(BigInteger, nullable=False)
    premium_frequency: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default=PolicyStatus.ACTIVE.value)
