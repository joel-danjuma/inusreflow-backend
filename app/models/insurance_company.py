import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.encryption import EncryptedString
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import OnboardingStatus, SettlementMode


class InsuranceCompany(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "insurance_companies"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'suspended')",
            name="ck_insurance_companies_status",
        ),
        CheckConstraint(
            "settlement_mode IN ('real_time', 'scheduled')",
            name="ck_insurance_companies_settlement_mode",
        ),
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    contact_email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=OnboardingStatus.PENDING.value
    )
    rejection_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    kyb_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    settlement_mode: Mapped[str] = mapped_column(
        String, nullable=False, default=SettlementMode.REAL_TIME.value
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Looked up and confirmed via Squad's Account Lookup API (PRD §8.6) --
    # never hand-entered freeform, so settlement_account_name is always
    # whatever Squad's own lookup returned for this bank_code/account_number
    # pair, not whatever the caller claims. NULL until set; settlement_service
    # fails closed (no payout) rather than guessing a destination.
    settlement_bank_code: Mapped[str | None] = mapped_column(String, nullable=True)
    settlement_account_number: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    settlement_account_name: Mapped[str | None] = mapped_column(String, nullable=True)
