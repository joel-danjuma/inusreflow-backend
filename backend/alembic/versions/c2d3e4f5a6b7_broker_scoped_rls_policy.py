"""broker scoped rls policy

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-07-28 09:05:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c2d3e4f5a6b7"
down_revision: str | Sequence[str] | None = "b1c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Tables with a direct broker_id column that brokers themselves may read --
#: settlement_payouts is deliberately excluded: it has no broker_id column,
#: and brokers never hold VIEW_SETTLEMENTS (app/rbac/permissions.py), so its
#: original insurer-only policy (see 2e2fb138e9eb) is left untouched.
_BROKER_SCOPED_TABLES = ("payments", "payment_batches", "policies", "policyholders")

#: Original policy clause from 2e2fb138e9eb, duplicated (not imported --
#: migrations are frozen-in-time, matching this repo's existing convention of
#: never importing across migration files) so downgrade() can restore it.
_TENANT_FILTER = (
    "NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL "
    "OR insurance_company_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid"
)

#: A broker with no explicit insurer selected now resolves to a tenant_id of
#: None (empty GUC) -- under the original _TENANT_FILTER alone that would be
#: misread as cross-tenant admin visibility. app.current_broker_id is a
#: second GUC, set to the broker's own stable broker_id on every broker-actor
#: request (never to a broker's dashboard-selected insurer -- that stays a
#: plain app-layer filter, layered on top of this RLS boundary, never fed
#: into current_tenant_id, or it would leak other brokers' rows under a
#: shared insurer). Only a *true* cross-tenant actor (both GUCs unset) hits
#: the first clause.
_TENANT_OR_BROKER_FILTER = (
    "(NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL "
    " AND NULLIF(current_setting('app.current_broker_id', true), '') IS NULL) "
    "OR insurance_company_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid "
    "OR broker_id = NULLIF(current_setting('app.current_broker_id', true), '')::uuid"
)


def upgrade() -> None:
    for table in _BROKER_SCOPED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            f"USING ({_TENANT_OR_BROKER_FILTER}) WITH CHECK ({_TENANT_OR_BROKER_FILTER})"
        )


def downgrade() -> None:
    for table in _BROKER_SCOPED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            f"USING ({_TENANT_FILTER}) WITH CHECK ({_TENANT_FILTER})"
        )
