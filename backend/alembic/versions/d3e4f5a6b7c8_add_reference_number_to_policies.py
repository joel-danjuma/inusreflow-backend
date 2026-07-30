"""add reference_number to policies

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-07-28 09:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3e4f5a6b7c8"
down_revision: str | Sequence[str] | None = "c2d3e4f5a6b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The insurer-supplied debit note / reference number that uniquely
    # identifies a policy. Nullable in the DB (pre-existing rows have no
    # value and no sane backfill); required at the API layer for every new
    # policy going forward (see PolicyCreateRequest), and genuinely unique --
    # unlike premium_installments.reference_number, which is deliberately
    # non-unique (see 68dc378a1938).
    op.add_column("policies", sa.Column("reference_number", sa.String(), nullable=True))
    op.create_index(
        "ux_policies_reference_number",
        "policies",
        ["reference_number"],
        unique=True,
        postgresql_where=sa.text("reference_number IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ux_policies_reference_number", table_name="policies")
    op.drop_column("policies", "reference_number")
