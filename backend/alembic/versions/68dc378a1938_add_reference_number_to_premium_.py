"""add reference_number to premium_installments

Revision ID: 68dc378a1938
Revises: c9e1f2a3b4d5
Create Date: 2026-07-20 01:04:46.452447

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "68dc378a1938"
down_revision: str | Sequence[str] | None = "c9e1f2a3b4d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # A real, externally-sourced Debit Note / reference number a broker or
    # insurer enters against a specific premium installment -- deliberately
    # no uniqueness constraint (real-world numbering across different
    # insurers could collide; duplicate detection happens at the app layer
    # during Excel-driven bulk-pay matching, not as a DB constraint that
    # could fail an unrelated insert).
    op.add_column(
        "premium_installments", sa.Column("reference_number", sa.String(), nullable=True)
    )
    op.create_index(
        "ix_premium_installments_reference_number",
        "premium_installments",
        ["reference_number"],
        postgresql_where=sa.text("reference_number IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_premium_installments_reference_number", table_name="premium_installments")
    op.drop_column("premium_installments", "reference_number")
