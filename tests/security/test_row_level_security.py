import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.insurance_company import InsuranceCompany

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
