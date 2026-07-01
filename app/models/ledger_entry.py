import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class LedgerEntry(UUIDPrimaryKeyMixin, Base):
    """Insert-only, immutable double-entry posting (PRD §8.7) — no
    update/delete codepath should ever be written against this table, same
    as AuditLog. amount_kobo is always positive; direction is carried by
    entry_type, never by sign.

    posting_group_id ties together every entry written by one call to
    post_ledger_entries — that's the unit `sum(debits) == sum(credits)` is
    asserted over, not the whole table.
    """

    __tablename__ = "ledger_entries"
    __table_args__ = (
        CheckConstraint("entry_type IN ('debit', 'credit')", name="ck_ledger_entries_entry_type"),
        CheckConstraint("amount_kobo > 0", name="ck_ledger_entries_amount_positive"),
        Index("ix_ledger_entries_posting_group_id", "posting_group_id"),
        Index("ix_ledger_entries_reference", "reference_type", "reference_id"),
    )

    ledger_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ledger_accounts.id"), nullable=False
    )
    entry_type: Mapped[str] = mapped_column(String, nullable=False)
    amount_kobo: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reference_type: Mapped[str] = mapped_column(String, nullable=False)
    reference_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    posting_group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
