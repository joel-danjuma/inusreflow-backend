"""seed initial insureflow admin

Revision ID: 37c595f4470a
Revises: 7a6cfa55a692
Create Date: 2026-06-22 20:55:51.624980

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.core.security import generate_activation_token

# revision identifiers, used by Alembic.
revision: str = "37c595f4470a"
down_revision: Sequence[str] | str | None = "7a6cfa55a692"
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None

ADMIN_EMAIL = "admin@insureflow.local"


def upgrade() -> None:
    """Bootstraps the first Insureflow Admin so there is someone to approve the
    first insurance company/broker onboarding — without this row, the
    approval workflow has no valid actor to start from. Inactive until
    activated via the printed one-time token, same as any other admin.
    """
    raw_token, token_hash, expires_at = generate_activation_token()
    platform_users = sa.table(
        "platform_users",
        sa.column("id", sa.UUID()),
        sa.column("email", sa.String()),
        sa.column("role", sa.String()),
        sa.column("is_active", sa.Boolean()),
        sa.column("activation_token_hash", sa.String()),
        sa.column("activation_token_expires_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(
        platform_users,
        [
            {
                "id": uuid.uuid4(),
                "email": ADMIN_EMAIL,
                "role": "insureflow_admin",
                "is_active": False,
                "activation_token_hash": token_hash,
                "activation_token_expires_at": expires_at,
            }
        ],
    )
    print(f"Bootstrap Insureflow Admin ({ADMIN_EMAIL}) activation token (shown once): {raw_token}")


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM platform_users WHERE email = :email").bindparams(email=ADMIN_EMAIL)
    )
