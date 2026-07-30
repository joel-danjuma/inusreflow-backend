"""add parent_company_id to insurance_companies

Revision ID: d88f50a147ed
Revises: 68dc378a1938
Create Date: 2026-07-20 01:32:12.576675

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d88f50a147ed"
down_revision: str | Sequence[str] | None = "68dc378a1938"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Organizational grouping only (e.g. "Leadway Assurance Life" under
    # parent "Leadway Assurance") -- each subsidiary remains a fully
    # independent tenant. Nullable, self-referential; no data migration
    # needed for existing flat companies.
    op.add_column(
        "insurance_companies", sa.Column("parent_company_id", sa.UUID(), nullable=True)
    )
    op.create_foreign_key(
        "fk_insurance_companies_parent_company_id",
        "insurance_companies",
        "insurance_companies",
        ["parent_company_id"],
        ["id"],
    )
    op.create_index(
        "ix_insurance_companies_parent_company_id",
        "insurance_companies",
        ["parent_company_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_insurance_companies_parent_company_id", table_name="insurance_companies")
    op.drop_constraint(
        "fk_insurance_companies_parent_company_id", "insurance_companies", type_="foreignkey"
    )
    op.drop_column("insurance_companies", "parent_company_id")
