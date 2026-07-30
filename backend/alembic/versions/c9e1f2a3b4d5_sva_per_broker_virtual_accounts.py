"""sva per broker permanent virtual accounts

Revision ID: c9e1f2a3b4d5
Revises: 869246395739
Create Date: 2026-07-14 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9e1f2a3b4d5"
down_revision: str | Sequence[str] | None = "869246395739"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # brokers: KYB fields needed for Business SVA creation + VA details
    op.add_column("brokers", sa.Column("bvn", sa.String(11), nullable=True))
    op.add_column("brokers", sa.Column("phone_number", sa.String(20), nullable=True))
    op.add_column("brokers", sa.Column("squad_va_number", sa.String(), nullable=True))
    op.add_column("brokers", sa.Column("squad_va_bank", sa.String(), nullable=True))
    op.add_column("brokers", sa.Column("squad_customer_identifier", sa.String(), nullable=True))

    # payments / payment_batches: Squad's own transaction_reference from webhook,
    # used for verify_transaction re-query (distinct from our internal squad_transaction_ref).
    op.add_column("payments", sa.Column("squad_webhook_tx_ref", sa.String(), nullable=True))
    op.add_column(
        "payment_batches", sa.Column("squad_webhook_tx_ref", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("payment_batches", "squad_webhook_tx_ref")
    op.drop_column("payments", "squad_webhook_tx_ref")
    op.drop_column("brokers", "squad_customer_identifier")
    op.drop_column("brokers", "squad_va_bank")
    op.drop_column("brokers", "squad_va_number")
    op.drop_column("brokers", "phone_number")
    op.drop_column("brokers", "bvn")
