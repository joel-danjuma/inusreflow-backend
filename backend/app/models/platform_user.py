import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PlatformUser(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The authenticated login identity. Distinct from Policyholder (PRD's "User"),
    which is a record brokers create/manage and never logs in — see CLAUDE.md.

    Insurance companies, brokers, and broker staff are provisioned active with
    hashed_password set to a one-time password (OTP) at creation time --
    must_change_password gates them until they set a real password via
    PATCH /auth/change-password (app/services/auth_service.py), independent of
    org-approval status (app/core/deps.py's require_full_access checks both).
    activation_token_hash/activation_token_expires_at remain nullable and are
    now only used by the one-time Insureflow Admin bootstrap seed migration
    (37c595f4470a_seed_initial_insureflow_admin.py) -- every other onboarding
    path has moved to OTP.
    """

    __tablename__ = "platform_users"
    __table_args__ = (
        CheckConstraint(
            "(role = 'insureflow_admin' AND insurance_company_id IS NULL AND broker_id IS NULL) OR "
            "(role = 'insurance_company_admin' AND insurance_company_id IS NOT NULL "
            "AND broker_id IS NULL) OR "
            "(role IN ('broker_admin', 'broker_staff') AND broker_id IS NOT NULL "
            "AND insurance_company_id IS NULL)",
            name="ck_platform_users_role_scope",
        ),
    )

    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    hashed_password: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    insurance_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurance_companies.id"), nullable=True
    )
    broker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brokers.id"), nullable=True
    )
    activation_token_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    activation_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    otp_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
