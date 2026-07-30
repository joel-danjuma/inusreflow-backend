import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CommissionConfig(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Versioned, scoped commission rates (PRD §9) — never updated in place.
    Changing a rate closes the active row (effective_to = now()) and inserts
    a new one, so a Payment's locked-in commission_config_id always resolves
    to the exact rates that applied at payment time, forever.

    Resolution order is broker -> insurance_company -> global (most specific
    wins); exactly one active (effective_to IS NULL) row may exist per scope
    key, enforced by the three partial unique indexes below.
    """

    __tablename__ = "commission_configs"
    __table_args__ = (
        CheckConstraint(
            "scope IN ('global', 'insurance_company', 'broker')",
            name="ck_commission_configs_scope",
        ),
        CheckConstraint(
            "(scope = 'global' AND insurance_company_id IS NULL AND broker_id IS NULL) OR "
            "(scope = 'insurance_company' AND insurance_company_id IS NOT NULL) OR "
            "(scope = 'broker' AND broker_id IS NOT NULL)",
            name="ck_commission_configs_scope_fk_consistency",
        ),
        Index(
            "ux_commission_configs_active_global",
            "scope",
            unique=True,
            postgresql_where=text("effective_to IS NULL AND scope = 'global'"),
        ),
        Index(
            "ux_commission_configs_active_insurer",
            "insurance_company_id",
            unique=True,
            postgresql_where=text("effective_to IS NULL AND scope = 'insurance_company'"),
        ),
        Index(
            "ux_commission_configs_active_broker",
            "broker_id",
            unique=True,
            postgresql_where=text("effective_to IS NULL AND scope = 'broker'"),
        ),
    )

    scope: Mapped[str] = mapped_column(String, nullable=False)
    insurance_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurance_companies.id"), nullable=True
    )
    broker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brokers.id"), nullable=True
    )
    gtbank_rate_bps: Mapped[int] = mapped_column(Integer, nullable=False)
    insureflow_rate_bps: Mapped[int] = mapped_column(Integer, nullable=False)
    broker_rate_bps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("platform_users.id"), nullable=True
    )
