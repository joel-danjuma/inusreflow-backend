"""add policy detail fields

Revision ID: 5aa02c18cd3e
Revises: d88f50a147ed
Create Date: 2026-07-22 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5aa02c18cd3e"
down_revision: str | Sequence[str] | None = "d88f50a147ed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # All nullable, additive-only fields captured on the redone Create Policy
    # form. duration_months is informational only -- it does not bound
    # installment generation (top_up_policy_installments keeps maintaining
    # its rolling window regardless), matching the deliberate decision not to
    # introduce a policy expiry/renewal concept that doesn't exist yet.
    op.add_column("policies", sa.Column("policy_name", sa.String(), nullable=True))
    op.add_column("policies", sa.Column("duration_months", sa.Integer(), nullable=True))
    op.add_column("policies", sa.Column("coverage_amount_kobo", sa.BigInteger(), nullable=True))
    op.add_column("policies", sa.Column("coverage_items", sa.Text(), nullable=True))
    op.add_column("policies", sa.Column("beneficiaries", sa.Text(), nullable=True))
    op.add_column("policies", sa.Column("broker_notes", sa.Text(), nullable=True))
    op.add_column("policies", sa.Column("internal_tags", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("policies", "internal_tags")
    op.drop_column("policies", "broker_notes")
    op.drop_column("policies", "beneficiaries")
    op.drop_column("policies", "coverage_items")
    op.drop_column("policies", "coverage_amount_kobo")
    op.drop_column("policies", "duration_months")
    op.drop_column("policies", "policy_name")
