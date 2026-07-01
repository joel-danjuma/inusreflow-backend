from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers import (
    onboard_and_approve_broker,
    onboard_and_approve_insurance_company,
    seed_and_activate_insureflow_admin,
)


async def test_insurance_company_onboard_approve_activate_login(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)

    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Acme Insurance",
        contact_email="admin@acme-insurance.example.com",
    )
    assert company["status"] == "approved"

    get_resp = await client.get(
        f"/api/v1/insurance-companies/{company['id']}", headers=company_headers
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == company["id"]


async def test_broker_onboard_approve_activate_login(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)

    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Acme Brokers",
        contact_email="admin@acme-brokers.example.com",
    )
    assert broker["status"] == "approved"

    get_resp = await client.get(f"/api/v1/brokers/{broker['id']}", headers=broker_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == broker["id"]


async def test_broker_admin_can_create_broker_staff(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)

    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Staffed Brokers",
        contact_email="admin@staffed-brokers.example.com",
    )

    staff_resp = await client.post(
        f"/api/v1/brokers/{broker['id']}/staff",
        json={"email": "staff@staffed-brokers.example.com"},
        headers=broker_headers,
    )
    assert staff_resp.status_code == 201, staff_resp.text
    assert "activation_token" in staff_resp.json()


async def test_insureflow_admin_rejects_insurance_company_with_reason(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)

    onboard_resp = await client.post(
        "/api/v1/insurance-companies",
        json={"name": "Shaky Insurance", "contact_email": "admin@shaky-insurance.example.com"},
    )
    assert onboard_resp.status_code == 201
    company = onboard_resp.json()

    reject_resp = await client.patch(
        f"/api/v1/admin/insurance-companies/{company['id']}/reject",
        json={"reason": "Incomplete KYB documentation"},
        headers=admin_headers,
    )
    assert reject_resp.status_code == 200, reject_resp.text
    rejected = reject_resp.json()
    assert rejected["status"] == "rejected"
    assert rejected["rejection_reason"] == "Incomplete KYB documentation"
