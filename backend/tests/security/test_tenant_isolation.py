from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fakes import FakeSquadClient
from tests.helpers import (
    onboard_and_approve_broker,
    onboard_and_approve_insurance_company,
    seed_and_activate_insureflow_admin,
)


async def test_insurance_company_admin_cannot_read_another_tenant(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)

    company_a, headers_a = await onboard_and_approve_insurance_company(
        client, admin_headers, name="Tenant A Insurance", contact_email="admin@tenant-a.example.com"
    )
    company_b, _headers_b = await onboard_and_approve_insurance_company(
        client, admin_headers, name="Tenant B Insurance", contact_email="admin@tenant-b.example.com"
    )

    own_resp = await client.get(f"/api/v1/insurance-companies/{company_a['id']}", headers=headers_a)
    assert own_resp.status_code == 200

    other_resp = await client.get(
        f"/api/v1/insurance-companies/{company_b['id']}", headers=headers_a
    )
    assert other_resp.status_code == 403


async def test_insureflow_admin_can_read_any_insurance_company(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)

    company, _headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Any Tenant Insurance",
        contact_email="admin@any-tenant.example.com",
    )

    resp = await client.get(f"/api/v1/insurance-companies/{company['id']}", headers=admin_headers)
    assert resp.status_code == 200


async def test_broker_admin_cannot_read_another_brokers_record(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)

    broker_a, headers_a = await onboard_and_approve_broker(
        client, admin_headers, name="Tenant A Brokers", contact_email="admin@broker-a.example.com"
    )
    broker_b, _headers_b = await onboard_and_approve_broker(
        client, admin_headers, name="Tenant B Brokers", contact_email="admin@broker-b.example.com"
    )

    own_resp = await client.get(f"/api/v1/brokers/{broker_a['id']}", headers=headers_a)
    assert own_resp.status_code == 200

    other_resp = await client.get(f"/api/v1/brokers/{broker_b['id']}", headers=headers_a)
    assert other_resp.status_code == 403
