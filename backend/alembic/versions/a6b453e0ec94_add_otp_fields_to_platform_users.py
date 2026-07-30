"""add otp fields to platform_users

Revision ID: a6b453e0ec94
Revises: 5aa02c18cd3e
Create Date: 2026-07-22 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a6b453e0ec94"
down_revision: str | Sequence[str] | None = "5aa02c18cd3e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Insurance companies, brokers, and broker staff now provision
    # hashed_password directly with a one-time password (OTP) at creation
    # time instead of waiting on an admin-minted activation token --
    # must_change_password gates them until a real password is set.
    op.add_column(
        "platform_users",
        sa.Column(
            "must_change_password", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "platform_users", sa.Column("otp_expires_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("platform_users", "otp_expires_at")
    op.drop_column("platform_users", "must_change_password")
