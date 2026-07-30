import uuid
from datetime import date

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fakes import FakeSquadClient
from tests.helpers import (
    assign_broker_to_insurer,
    create_policy,
    create_policyholder,
    onboard_and_approve_broker,
    onboard_and_approve_insurance_company,
    seed_and_activate_insureflow_admin,
)


async def _create_policyholder_and_policy(
    client: AsyncClient,
    company_headers: dict[str, str],
    *,
    broker_id: str,
    name: str,
    policy_type: str,
) -> dict:
    policyholder = await create_policyholder(
        client,
        company_headers,
        broker_id=broker_id,
        full_name=name,
        email=f"{uuid.uuid4()}@example.com",
    )
    return await create_policy(
        client,
        company_headers,
        broker_id=broker_id,
        policyholder_id=policyholder["id"],
        reference_number=f"DN-{uuid.uuid4()}",
        premium_amount_kobo=100_000,
        start_date=date.today().isoformat(),
        policy_type=policy_type,
    )


async def test_installments_filter_by_policy_type(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Policy Type Filter Insurance",
        contact_email=f"admin-{uuid.uuid4()}@policy-type-filter-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Policy Type Filter Brokers",
        contact_email=f"admin-{uuid.uuid4()}@policy-type-filter-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )

    auto_policy = await _create_policyholder_and_policy(
        client, company_headers, broker_id=broker["id"], name="Auto Client", policy_type="AUTO"
    )
    health_policy = await _create_policyholder_and_policy(
        client, company_headers, broker_id=broker["id"], name="Health Client", policy_type="HEALTH"
    )

    all_resp = await client.get("/api/v1/installments", headers=broker_headers)
    assert all_resp.status_code == 200, all_resp.text
    all_policy_ids = {i["policy_id"] for i in all_resp.json()}
    assert auto_policy["id"] in all_policy_ids
    assert health_policy["id"] in all_policy_ids
    assert all(i["policy_type"] in ("AUTO", "HEALTH") for i in all_resp.json())

    auto_resp = await client.get(
        "/api/v1/installments", params={"policy_type": "auto"}, headers=broker_headers
    )
    assert auto_resp.status_code == 200, auto_resp.text
    auto_installments = auto_resp.json()
    assert len(auto_installments) > 0
    assert all(i["policy_id"] == auto_policy["id"] for i in auto_installments)
    assert all(i["policy_type"] == "AUTO" for i in auto_installments)

    health_resp = await client.get(
        "/api/v1/installments", params={"policy_type": "HEALTH"}, headers=broker_headers
    )
    assert health_resp.status_code == 200, health_resp.text
    health_installments = health_resp.json()
    assert len(health_installments) > 0
    assert all(i["policy_id"] == health_policy["id"] for i in health_installments)


async def test_set_installment_reference_number_broker_and_insurer(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Reference Number Insurance",
        contact_email=f"admin-{uuid.uuid4()}@reference-number-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Reference Number Brokers",
        contact_email=f"admin-{uuid.uuid4()}@reference-number-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )
    policy = await _create_policyholder_and_policy(
        client, company_headers, broker_id=broker["id"], name="Ref Client", policy_type="AUTO"
    )
    installments_resp = await client.get(
        f"/api/v1/policies/{policy['id']}/installments", headers=broker_headers
    )
    installment_id = installments_resp.json()[0]["id"]

    # Broker sets it.
    set_resp = await client.patch(
        f"/api/v1/installments/{installment_id}/reference-number",
        json={"reference_number": "DN-00123"},
        headers=broker_headers,
    )
    assert set_resp.status_code == 200, set_resp.text
    assert set_resp.json()["reference_number"] == "DN-00123"

    # Insurer can also update it.
    update_resp = await client.patch(
        f"/api/v1/installments/{installment_id}/reference-number",
        json={"reference_number": "DN-00456"},
        headers=company_headers,
    )
    assert update_resp.status_code == 200, update_resp.text
    assert update_resp.json()["reference_number"] == "DN-00456"

    # Clearing it back to null.
    clear_resp = await client.patch(
        f"/api/v1/installments/{installment_id}/reference-number",
        json={"reference_number": None},
        headers=broker_headers,
    )
    assert clear_resp.status_code == 200, clear_resp.text
    assert clear_resp.json()["reference_number"] is None


async def test_set_installment_reference_number_forbidden_cross_tenant(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company_a, company_a_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Reference Cross Tenant Insurance A",
        contact_email=f"admin-{uuid.uuid4()}@reference-cross-a.example.com",
    )
    broker_a, broker_a_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Reference Cross Tenant Broker A",
        contact_email=f"admin-{uuid.uuid4()}@reference-cross-broker-a.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker_a["id"], insurance_company_id=company_a["id"]
    )
    policy = await _create_policyholder_and_policy(
        client,
        company_a_headers,
        broker_id=broker_a["id"],
        name="Cross Tenant Client",
        policy_type="AUTO",
    )
    installments_resp = await client.get(
        f"/api/v1/policies/{policy['id']}/installments", headers=broker_a_headers
    )
    installment_id = installments_resp.json()[0]["id"]

    broker_b, broker_b_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Reference Cross Tenant Broker B",
        contact_email=f"admin-{uuid.uuid4()}@reference-cross-broker-b.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker_b["id"], insurance_company_id=company_a["id"]
    )
    # Now 404, not 403: RLS scopes a broker's visibility into `policies` by
    # their own broker_id (docs/adr/0011-broker-insurer-many-to-many.md), so
    # broker_b's session can no longer even read broker_a's policy row --
    # the app-layer ownership check in _check_installment_access never gets
    # a chance to run, since db.get(Policy, ...) already returns None.
    forbidden_resp = await client.patch(
        f"/api/v1/installments/{installment_id}/reference-number",
        json={"reference_number": "DN-SHOULD-NOT-WORK"},
        headers=broker_b_headers,
    )
    assert forbidden_resp.status_code == 404, forbidden_resp.text
