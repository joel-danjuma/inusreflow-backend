import uuid
from typing import Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.encryption import EncryptedString
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Policyholder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """PRD's "User" — a data record a broker creates/manages, never an
    authenticated login (see PlatformUser for that distinction).

    insurance_company_id is denormalized from the broker's active
    broker_insurer_assignments row at creation time, for fast tenant-scoped
    queries without a join on every request.
    """

    __tablename__ = "policyholders"

    broker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brokers.id"), nullable=False
    )
    insurance_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurance_companies.id"), nullable=False
    )
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String, nullable=True)
    identification_number: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)
