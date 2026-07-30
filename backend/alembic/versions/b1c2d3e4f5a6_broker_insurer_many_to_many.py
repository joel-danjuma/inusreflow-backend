"""broker insurer many to many

Revision ID: b1c2d3e4f5a6
Revises: a6b453e0ec94
Create Date: 2026-07-28 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: str | Sequence[str] | None = "a6b453e0ec94"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Was a partial unique index on broker_id alone (at most one active
    # assignment per broker, system-wide). Replaced with a composite index on
    # the (broker, insurer) pair: a given pair still can't be double-active,
    # but a broker may now have many different pairs active simultaneously.
    op.drop_index(
        "ux_broker_insurer_assignments_active_broker",
        table_name="broker_insurer_assignments",
    )
    op.create_index(
        "ux_broker_insurer_assignments_active_pair",
        "broker_insurer_assignments",
        ["broker_id", "insurance_company_id"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )


def downgrade() -> None:
    op.drop_index(
        "ux_broker_insurer_assignments_active_pair",
        table_name="broker_insurer_assignments",
    )
    op.create_index(
        "ux_broker_insurer_assignments_active_broker",
        "broker_insurer_assignments",
        ["broker_id"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )
