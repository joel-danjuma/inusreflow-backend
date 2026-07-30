import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

#: GTBANK_REVENUE/INSUREFLOW_REVENUE are platform-wide singletons (no
#: insurance_company_id/broker_id); BROKER_CLEARING/BROKER_COMMISSION are
#: per-broker; INSURER_PAYABLE/INSURER_SETTLED are per-insurer (PRD §8.7).
ACCOUNT_TYPES = (
    "BROKER_CLEARING",
    "GTBANK_REVENUE",
    "INSUREFLOW_REVENUE",
    "BROKER_COMMISSION",
    "INSURER_PAYABLE",
    "INSURER_SETTLED",
)


class LedgerAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A ledger account never carries a balance field — its balance is always
    the sum of its LedgerEntry rows, computed on read. The partial unique
    indexes below guarantee get-or-create never races into duplicate
    accounts for the same (account_type, scope) key.
    """

    __tablename__ = "ledger_accounts"
    __table_args__ = (
        CheckConstraint(
            "account_type IN ('BROKER_CLEARING', 'GTBANK_REVENUE', 'INSUREFLOW_REVENUE', "
            "'BROKER_COMMISSION', 'INSURER_PAYABLE', 'INSURER_SETTLED')",
            name="ck_ledger_accounts_account_type",
        ),
        Index(
            "ux_ledger_accounts_platform",
            "account_type",
            unique=True,
            postgresql_where=text("insurance_company_id IS NULL AND broker_id IS NULL"),
        ),
        Index(
            "ux_ledger_accounts_broker",
            "account_type",
            "broker_id",
            unique=True,
            postgresql_where=text("broker_id IS NOT NULL"),
        ),
        Index(
            "ux_ledger_accounts_insurer",
            "account_type",
            "insurance_company_id",
            unique=True,
            postgresql_where=text("insurance_company_id IS NOT NULL AND broker_id IS NULL"),
        ),
    )

    account_type: Mapped[str] = mapped_column(String, nullable=False)
    insurance_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurance_companies.id"), nullable=True
    )
    broker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brokers.id"), nullable=True
    )
