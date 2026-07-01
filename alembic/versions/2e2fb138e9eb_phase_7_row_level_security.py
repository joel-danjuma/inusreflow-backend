"""phase 7 row level security

Revision ID: 2e2fb138e9eb
Revises: de5210a3756a
Create Date: 2026-06-23 22:56:48.246381

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2e2fb138e9eb"
down_revision: str | Sequence[str] | None = "de5210a3756a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Local-dev-only credential, mirroring Settings.jwt_secret_key's existing
#: pattern -- a real deploy rotates this via ALTER ROLE from a secrets
#: manager, never from source control (docs/adr/0006-row-level-security.md).
_APP_ROLE = "insureflow_app"
_APP_ROLE_PASSWORD = "insureflow_app_local_dev_only"  # noqa: S105

#: Tables with a direct, non-nullable insurance_company_id column owned by
#: exactly one tenant. Tables where tenant ownership is nullable/ambiguous
#: (commission_configs, ledger_accounts -- a NULL insurance_company_id is a
#: legitimate global/platform row, not a leak) or only reachable via a join
#: (premium_installments, reminders, payment_batch_items, ledger_entries) are
#: deliberately out of scope for this pass -- see the ADR.
_TENANT_SCOPED_TABLES = (
    "payments",
    "payment_batches",
    "policies",
    "policyholders",
    "settlement_payouts",
)

#: NULLIF folds both "unset" (current_setting returns NULL) and "explicitly
#: empty" (set_config(..., '', true), used for cross-tenant/admin contexts)
#: into a single NULL before the ::uuid cast ever runs. Casting the *branch*
#: of an OR instead -- e.g. "x = '' OR y = x::uuid" -- is unsafe: Postgres's
#: planner is free to reorder OR'd quals by estimated cost and evaluate the
#: cast branch first, so an empty string can reach ''::uuid and raise
#: invalid_text_representation even though the empty-string guard appears
#: earlier in the source text.
_TENANT_FILTER = (
    "NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL "
    "OR insurance_company_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid"
)


def upgrade() -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{_APP_ROLE}') THEN
                CREATE ROLE {_APP_ROLE} WITH LOGIN PASSWORD '{_APP_ROLE_PASSWORD}';
            END IF;
        END
        $$;
        """
    )
    op.execute(
        f"""
        DO $$
        BEGIN
            EXECUTE format('GRANT CONNECT ON DATABASE %I TO {_APP_ROLE}', current_database());
        END
        $$;
        """
    )
    op.execute(f"GRANT USAGE ON SCHEMA public TO {_APP_ROLE}")
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {_APP_ROLE}"
    )
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {_APP_ROLE}"
    )

    for table in _TENANT_SCOPED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        # Table owner (the migration role) would otherwise be exempt from its
        # own RLS policies -- FORCE closes that gap too, belt-and-suspenders
        # alongside connecting at runtime as the non-owning insureflow_app role.
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            f"USING ({_TENANT_FILTER}) WITH CHECK ({_TENANT_FILTER})"
        )


def downgrade() -> None:
    for table in _TENANT_SCOPED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM {_APP_ROLE}"
    )
    op.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {_APP_ROLE}")
    op.execute(f"REVOKE USAGE ON SCHEMA public FROM {_APP_ROLE}")
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM pg_roles WHERE rolname = '{_APP_ROLE}') THEN
                EXECUTE format(
                    'REVOKE CONNECT ON DATABASE %I FROM {_APP_ROLE}', current_database()
                );
                DROP OWNED BY {_APP_ROLE};
                DROP ROLE {_APP_ROLE};
            END IF;
        END
        $$;
        """
    )
