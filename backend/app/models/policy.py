import uuid
from datetime import date

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import PolicyStatus

DEFAULT_POLICY_TYPE = "GENERIC"


class Policy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """policy_type is an open string seeded 'GENERIC', never a fixed enum, per
    CLAUDE.md. broker_id/insurance_company_id are denormalized from the owning
    policyholder for fast tenant/broker-scoped queries.

    reference_number is the insurer-supplied debit note number that uniquely
    identifies this policy as a business record -- required by the API on
    every new policy (see PolicyCreateRequest), but nullable in the DB since
    rows created before this field existed have no value and no sane
    backfill. Distinct from, and unrelated to, PremiumInstallment's own
    per-installment reference_number (used for Excel bulk-pay matching).
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
        Index(
            "ux_policies_reference_number",
            "reference_number",
            unique=True,
            postgresql_where=text("reference_number IS NOT NULL"),
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

    # Free-form detail fields captured on the Create Policy form -- all
    # nullable/optional, none of them feed into installment generation or any
    # other service logic (duration_months in particular is informational
    # only: top_up_policy_installments keeps maintaining its rolling window
    # regardless, there is no policy expiry/renewal concept yet).
    policy_name: Mapped[str | None] = mapped_column(String, nullable=True)
    duration_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    coverage_amount_kobo: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    coverage_items: Mapped[str | None] = mapped_column(Text, nullable=True)
    beneficiaries: Mapped[str | None] = mapped_column(Text, nullable=True)
    broker_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_tags: Mapped[str | None] = mapped_column(String, nullable=True)
    reference_number: Mapped[str | None] = mapped_column(String, nullable=True)
