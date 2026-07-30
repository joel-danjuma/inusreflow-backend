import uuid

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.broker import Broker
from app.models.insurance_company import InsuranceCompany
from app.models.policyholder import Policyholder

_INSERT_PAYOUT = text(
    """
    INSERT INTO settlement_payouts
        (id, insurance_company_id, source_type, source_id, amount_kobo, status,
         squad_transfer_ref, attempt_number)
    VALUES
        (:id, :insurance_company_id, 'payment', :source_id, 10000, 'success', :ref, 1)
    """
)


async def _set_tenant_context(db_session: AsyncSession, tenant_id: uuid.UUID | str) -> None:
    await db_session.execute(
        text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id)},
    )


async def _seed_two_companies(
    db_session: AsyncSession,
) -> tuple[InsuranceCompany, InsuranceCompany]:
    company_a = InsuranceCompany(name="RLS Tenant A", contact_email=f"{uuid.uuid4()}@example.com")
    company_b = InsuranceCompany(name="RLS Tenant B", contact_email=f"{uuid.uuid4()}@example.com")
    db_session.add_all([company_a, company_b])
    await db_session.flush()
    return company_a, company_b


async def test_rls_blocks_cross_tenant_select_on_settlement_payouts(
    db_session: AsyncSession,
) -> None:
    """Proves the database itself, not just app-layer query filtering, keeps
    one insurer's settlement payouts invisible to another's session -- the
    insert and both reads run as insureflow_app (the restricted runtime
    role, app/core/db.py), the same role real requests use, bypassing the
    service/repository layer entirely so a bug there couldn't mask a no-op
    policy (docs/adr/0006-row-level-security.md).
    """
    company_a, company_b = await _seed_two_companies(db_session)

    await _set_tenant_context(db_session, company_a.id)
    payout_id = uuid.uuid4()
    await db_session.execute(
        _INSERT_PAYOUT,
        {
            "id": payout_id,
            "insurance_company_id": company_a.id,
            "source_id": uuid.uuid4(),
            "ref": f"rls-test-{uuid.uuid4()}",
        },
    )

    visible_to_a = await db_session.execute(
        text("SELECT id FROM settlement_payouts WHERE id = :id"), {"id": payout_id}
    )
    assert visible_to_a.scalar() == payout_id

    await _set_tenant_context(db_session, company_b.id)
    visible_to_b = await db_session.execute(
        text("SELECT id FROM settlement_payouts WHERE id = :id"), {"id": payout_id}
    )
    assert visible_to_b.scalar() is None


async def test_rls_allows_unrestricted_access_when_tenant_context_is_unset(
    db_session: AsyncSession,
) -> None:
    """An unset/empty GUC -- Celery tasks, reconciliation, Insureflow Admin --
    is cross-tenant by design, not a default-deny (docs/adr/0006-row-level-security.md).
    """
    company_a, _ = await _seed_two_companies(db_session)

    await _set_tenant_context(db_session, company_a.id)
    payout_id = uuid.uuid4()
    await db_session.execute(
        _INSERT_PAYOUT,
        {
            "id": payout_id,
            "insurance_company_id": company_a.id,
            "source_id": uuid.uuid4(),
            "ref": f"rls-test-{uuid.uuid4()}",
        },
    )

    await _set_tenant_context(db_session, "")
    result = await db_session.execute(
        text("SELECT id FROM settlement_payouts WHERE id = :id"), {"id": payout_id}
    )
    assert result.scalar() == payout_id


async def test_rls_rejects_cross_tenant_insert_via_with_check(db_session: AsyncSession) -> None:
    """The WITH CHECK clause, not just USING, is enforced -- a session scoped
    to tenant B can't write a row claiming to belong to tenant A.
    """
    company_a, company_b = await _seed_two_companies(db_session)

    await _set_tenant_context(db_session, company_b.id)
    # A SAVEPOINT, not the outer transaction the db_session fixture manages --
    # exiting on the expected error rolls back only this statement, leaving
    # the rest of the test/fixture teardown unaffected.
    with pytest.raises(DBAPIError, match="row-level security"):
        async with db_session.begin_nested():
            await db_session.execute(
                _INSERT_PAYOUT,
                {
                    "id": uuid.uuid4(),
                    "insurance_company_id": company_a.id,
                    "source_id": uuid.uuid4(),
                    "ref": f"rls-test-{uuid.uuid4()}",
                },
            )


# --- Broker-scoped RLS (docs/adr/0011-broker-insurer-many-to-many.md) ---
#
# The four tables below also key off app.current_broker_id, in addition to
# app.current_tenant_id -- these tests target `policyholders` specifically
# because it needs no FK chain beyond a Broker/InsuranceCompany row (unlike
# `payments`, which also requires a real installment/commission_config row).
# The risk being guarded against is documented in the ADR: a broker actor's
# get_tenant_id now always resolves tenant_id=None, and if RLS treated that
# the same as "both GUCs unset" (the true admin/cross-tenant case), a broker
# would gain unrestricted cross-tenant visibility.

_INSERT_POLICYHOLDER = text(
    """
    INSERT INTO policyholders (id, broker_id, insurance_company_id, full_name)
    VALUES (:id, :broker_id, :insurance_company_id, :full_name)
    """
)


async def _set_broker_context(db_session: AsyncSession, broker_id: uuid.UUID | str) -> None:
    """Mirrors _set_tenant_context, but for the broker-side GUC -- leaves
    app.current_tenant_id unset, exactly as app/core/deps.py::get_tenant_id
    does for a broker actor.
    """
    await db_session.execute(
        text("SELECT set_config('app.current_broker_id', :broker_id, true)"),
        {"broker_id": str(broker_id)},
    )


async def _seed_broker_with_policyholder(
    db_session: AsyncSession, *, company_id: uuid.UUID, name: str
) -> tuple[Broker, uuid.UUID]:
    """Seeds a Broker (unprotected table, no RLS) and one Policyholder row
    for it. Run before any GUC is set in the test, so the insert itself
    hits RLS's "both unset -> unrestricted" branch, same as any other
    trusted-internal seeding in this file.
    """
    broker = Broker(name=name, contact_email=f"{uuid.uuid4()}@example.com")
    db_session.add(broker)
    await db_session.flush()

    policyholder_id = uuid.uuid4()
    await db_session.execute(
        _INSERT_POLICYHOLDER,
        {
            "id": policyholder_id,
            "broker_id": broker.id,
            "insurance_company_id": company_id,
            "full_name": f"{name} Client",
        },
    )
    return broker, policyholder_id


async def test_rls_broker_guc_grants_visibility_to_own_rows(db_session: AsyncSession) -> None:
    company, _ = await _seed_two_companies(db_session)
    broker_a, policyholder_a_id = await _seed_broker_with_policyholder(
        db_session, company_id=company.id, name="RLS Broker A"
    )

    await _set_broker_context(db_session, broker_a.id)
    result = await db_session.scalar(
        select(Policyholder.id).where(Policyholder.id == policyholder_a_id)
    )
    assert result == policyholder_a_id


async def test_rls_broker_guc_does_not_grant_visibility_into_a_different_brokers_rows(
    db_session: AsyncSession,
) -> None:
    """The specific trap the ADR calls out: both brokers work with the same
    insurer, but app.current_broker_id must still isolate them from each
    other -- insurance_company_id alone is not the boundary for a broker.
    """
    company, _ = await _seed_two_companies(db_session)
    broker_a, _ = await _seed_broker_with_policyholder(
        db_session, company_id=company.id, name="RLS Broker A2"
    )
    _broker_b, policyholder_b_id = await _seed_broker_with_policyholder(
        db_session, company_id=company.id, name="RLS Broker B2"
    )

    await _set_broker_context(db_session, broker_a.id)
    result = await db_session.scalar(
        select(Policyholder.id).where(Policyholder.id == policyholder_b_id)
    )
    assert result is None


async def test_rls_with_check_rejects_insert_claiming_a_mismatched_broker_id(
    db_session: AsyncSession,
) -> None:
    company, _ = await _seed_two_companies(db_session)
    _broker_a, _ = await _seed_broker_with_policyholder(
        db_session, company_id=company.id, name="RLS Broker A3"
    )
    broker_b = Broker(name="RLS Broker B3", contact_email=f"{uuid.uuid4()}@example.com")
    db_session.add(broker_b)
    await db_session.flush()

    await _set_broker_context(db_session, broker_b.id)
    with pytest.raises(DBAPIError, match="row-level security"):
        async with db_session.begin_nested():
            # Session is scoped to broker_b, but the row claims broker_a's
            # (now out-of-scope) broker_id -- WITH CHECK must reject it.
            await db_session.execute(
                _INSERT_POLICYHOLDER,
                {
                    "id": uuid.uuid4(),
                    "broker_id": uuid.uuid4(),
                    "insurance_company_id": company.id,
                    "full_name": "Should Not Insert",
                },
            )


async def test_rls_both_gucs_unset_still_means_cross_tenant(db_session: AsyncSession) -> None:
    """Regression guard on existing insureflow_admin/Celery-task behavior --
    the 3-clause policy's first branch must still require BOTH GUCs unset,
    not just one, to grant unrestricted visibility.
    """
    company, _ = await _seed_two_companies(db_session)
    _broker, policyholder_id = await _seed_broker_with_policyholder(
        db_session, company_id=company.id, name="RLS Unset Guard"
    )

    await db_session.execute(
        text(
            "SELECT set_config('app.current_tenant_id', '', true), "
            "set_config('app.current_broker_id', '', true)"
        )
    )
    result = await db_session.scalar(
        select(Policyholder.id).where(Policyholder.id == policyholder_id)
    )
    assert result == policyholder_id
