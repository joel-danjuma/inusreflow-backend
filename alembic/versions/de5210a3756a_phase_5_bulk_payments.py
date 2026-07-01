"""phase 5 bulk payments

Revision ID: de5210a3756a
Revises: 14d15d5ad668
Create Date: 2026-06-23 19:30:33.699527

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "de5210a3756a"
down_revision: str | Sequence[str] | None = "14d15d5ad668"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # payment_batches must exist before payment_batch_items (which FKs into
    # it) -- moved ahead of autogenerate's alphabetical table order, same
    # adjustment the Phase 4 migration made for idempotency_keys/payments.
    op.create_table(
        "payment_batches",
        sa.Column("broker_id", sa.UUID(), nullable=False),
        sa.Column("insurance_company_id", sa.UUID(), nullable=False),
        sa.Column("initiated_by", sa.UUID(), nullable=False),
        sa.Column("commission_config_id", sa.UUID(), nullable=False),
        sa.Column("idempotency_key_id", sa.UUID(), nullable=True),
        sa.Column("total_amount_kobo", sa.BigInteger(), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("squad_transaction_ref", sa.String(), nullable=False),
        sa.Column("squad_virtual_account_number", sa.String(), nullable=True),
        sa.Column("squad_virtual_account_bank", sa.String(), nullable=True),
        sa.Column("va_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.String(), nullable=True),
        sa.Column("raw_squad_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('initiated', 'success', 'mismatch', 'expired', 'failed')",
            name="ck_payment_batches_status",
        ),
        sa.CheckConstraint("item_count > 0", name="ck_payment_batches_item_count_positive"),
        sa.ForeignKeyConstraint(["broker_id"], ["brokers.id"]),
        sa.ForeignKeyConstraint(["commission_config_id"], ["commission_configs.id"]),
        sa.ForeignKeyConstraint(["idempotency_key_id"], ["idempotency_keys.id"]),
        sa.ForeignKeyConstraint(["initiated_by"], ["platform_users.id"]),
        sa.ForeignKeyConstraint(["insurance_company_id"], ["insurance_companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("squad_transaction_ref"),
    )
    op.create_index(
        "ix_payment_batches_broker_id_status", "payment_batches", ["broker_id", "status"]
    )
    op.create_table(
        "payment_batch_items",
        sa.Column("payment_batch_id", sa.UUID(), nullable=False),
        sa.Column("installment_id", sa.UUID(), nullable=False),
        sa.Column("amount_kobo", sa.BigInteger(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["installment_id"], ["premium_installments.id"]),
        sa.ForeignKeyConstraint(["payment_batch_id"], ["payment_batches.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "payment_batch_id",
            "installment_id",
            name="ux_payment_batch_items_batch_installment",
        ),
    )
    op.add_column(
        "premium_installments", sa.Column("payment_batch_item_id", sa.UUID(), nullable=True)
    )
    op.create_foreign_key(
        "fk_premium_installments_payment_batch_item_id",
        "premium_installments",
        "payment_batch_items",
        ["payment_batch_item_id"],
        ["id"],
    )
    op.create_check_constraint(
        "ck_premium_installments_payment_xor_batch_item",
        "premium_installments",
        "NOT (payment_id IS NOT NULL AND payment_batch_item_id IS NOT NULL)",
    )
    op.drop_constraint("ck_settlement_payouts_source_type", "settlement_payouts", type_="check")
    op.create_check_constraint(
        "ck_settlement_payouts_source_type",
        "settlement_payouts",
        "source_type IN ('payment', 'payment_batch')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_settlement_payouts_source_type", "settlement_payouts", type_="check")
    op.create_check_constraint(
        "ck_settlement_payouts_source_type",
        "settlement_payouts",
        "source_type IN ('payment')",
    )
    op.drop_constraint(
        "ck_premium_installments_payment_xor_batch_item",
        "premium_installments",
        type_="check",
    )
    op.drop_constraint(
        "fk_premium_installments_payment_batch_item_id",
        "premium_installments",
        type_="foreignkey",
    )
    op.drop_column("premium_installments", "payment_batch_item_id")
    op.drop_table("payment_batch_items")
    op.drop_index("ix_payment_batches_broker_id_status", table_name="payment_batches")
    op.drop_table("payment_batches")
