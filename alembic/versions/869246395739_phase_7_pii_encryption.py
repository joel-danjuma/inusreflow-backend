"""phase 7 pii encryption

Revision ID: 869246395739
Revises: 2e2fb138e9eb
Create Date: 2026-06-23 23:20:19.092793

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "869246395739"
down_revision: str | Sequence[str] | None = "2e2fb138e9eb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Must match Settings.pii_encryption_key's local-dev default
#: (app/core/config.py, docs/adr/0007-pii-encryption.md). Only used here to
#: convert any *existing* plaintext rows at migration time -- both tables
#: are empty in every environment this has run against so far, so this is a
#: safety net, not a verified production backfill path. Rotating the real
#: key later requires decrypting with the old key and re-encrypting with the
#: new one first; a bare Settings change alone would orphan existing rows.
_PII_ENCRYPTION_KEY = "local-dev-pii-key-change-me-please-this-is-not-for-prod"

_APP_ROLE = "insureflow_app"


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.execute(
        f"ALTER TABLE policyholders ALTER COLUMN identification_number TYPE bytea "
        f"USING pgp_sym_encrypt(identification_number, '{_PII_ENCRYPTION_KEY}')"
    )
    op.execute(
        f"ALTER TABLE insurance_companies ALTER COLUMN settlement_account_number TYPE bytea "
        f"USING pgp_sym_encrypt(settlement_account_number, '{_PII_ENCRYPTION_KEY}')"
    )

    # pgcrypto's functions are owned by whichever role ran CREATE EXTENSION
    # (the migration role, not insureflow_app) -- explicit grants here rather
    # than relying on PUBLIC's default EXECUTE privilege staying unrevoked.
    op.execute(f"GRANT EXECUTE ON FUNCTION pgp_sym_encrypt(text, text) TO {_APP_ROLE}")
    op.execute(f"GRANT EXECUTE ON FUNCTION pgp_sym_decrypt(bytea, text) TO {_APP_ROLE}")


def downgrade() -> None:
    op.execute(
        f"ALTER TABLE policyholders ALTER COLUMN identification_number TYPE varchar "
        f"USING pgp_sym_decrypt(identification_number, '{_PII_ENCRYPTION_KEY}')"
    )
    op.execute(
        f"ALTER TABLE insurance_companies ALTER COLUMN settlement_account_number TYPE varchar "
        f"USING pgp_sym_decrypt(settlement_account_number, '{_PII_ENCRYPTION_KEY}')"
    )
