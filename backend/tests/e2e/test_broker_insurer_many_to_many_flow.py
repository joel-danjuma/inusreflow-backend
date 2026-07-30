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


async def test_broker_can_be_assigned_two_insurers_simultaneously(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company_a, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="M2M Insurer A",
        contact_email=f"a-{uuid.uuid4()}@m2m.example.com",
    )
    company_b, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="M2M Insurer B",
        contact_email=f"b-{uuid.uuid4()}@m2m.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="M2M Broker",
        contact_email=f"broker-{uuid.uuid4()}@m2m.example.com",
    )

    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company_a["id"]
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company_b["id"]
    )

    insurers_resp = await client.get(
        f"/api/v1/brokers/{broker['id']}/insurers", headers=broker_headers
    )
    assert insurers_resp.status_code == 200, insurers_resp.text
    insurer_ids = {i["id"] for i in insurers_resp.json()}
    assert insurer_ids == {company_a["id"], company_b["id"]}


async def test_broker_dashboard_aggregates_by_default_and_narrows_with_insurer_id(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company_a, company_a_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="M2M Dash Insurer A",
        contact_email=f"a-{uuid.uuid4()}@m2m-dash.example.com",
    )
    company_b, company_b_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="M2M Dash Insurer B",
        contact_email=f"b-{uuid.uuid4()}@m2m-dash.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="M2M Dash Broker",
        contact_email=f"broker-{uuid.uuid4()}@m2m-dash.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company_a["id"]
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company_b["id"]
    )

    policyholder_a = await create_policyholder(
        client, company_a_headers, broker_id=broker["id"], full_name="A Client"
    )
    policy_a = await create_policy(
        client,
        company_a_headers,
        broker_id=broker["id"],
        policyholder_id=policyholder_a["id"],
        reference_number=f"DN-{uuid.uuid4()}",
        start_date=date.today().isoformat(),
    )
    policyholder_b = await create_policyholder(
        client, company_b_headers, broker_id=broker["id"], full_name="B Client"
    )
    policy_b = await create_policy(
        client,
        company_b_headers,
        broker_id=broker["id"],
        policyholder_id=policyholder_b["id"],
        reference_number=f"DN-{uuid.uuid4()}",
        start_date=date.today().isoformat(),
    )

    # Aggregate by default: both policies' installments show up.
    all_resp = await client.get("/api/v1/installments", headers=broker_headers)
    assert all_resp.status_code == 200, all_resp.text
    all_policy_ids = {i["policy_id"] for i in all_resp.json()}
    assert policy_a["id"] in all_policy_ids
    assert policy_b["id"] in all_policy_ids

    # Narrowed to insurer A: only policy A's installments.
    narrowed_a = await client.get(
        "/api/v1/installments", headers=broker_headers, params={"insurer_id": company_a["id"]}
    )
    assert narrowed_a.status_code == 200, narrowed_a.text
    narrowed_a_policy_ids = {i["policy_id"] for i in narrowed_a.json()}
    assert policy_a["id"] in narrowed_a_policy_ids
    assert policy_b["id"] not in narrowed_a_policy_ids

    # Narrowed to insurer B: only policy B's installments.
    narrowed_b = await client.get(
        "/api/v1/installments", headers=broker_headers, params={"insurer_id": company_b["id"]}
    )
    assert narrowed_b.status_code == 200, narrowed_b.text
    narrowed_b_policy_ids = {i["policy_id"] for i in narrowed_b.json()}
    assert policy_b["id"] in narrowed_b_policy_ids
    assert policy_a["id"] not in narrowed_b_policy_ids

    # Narrowing to an insurer the broker isn't assigned to 404s.
    company_c, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="M2M Dash Insurer C Unassigned",
        contact_email=f"c-{uuid.uuid4()}@m2m-dash.example.com",
    )
    forbidden_resp = await client.get(
        "/api/v1/installments", headers=broker_headers, params={"insurer_id": company_c["id"]}
    )
    assert forbidden_resp.status_code == 404, forbidden_resp.text


async def test_payment_against_either_assigned_insurers_policy_settles_to_correct_insurer(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """Money-movement correctness (docs/adr/0011-broker-insurer-many-to-many.md):
    a payment's insurer is derived from the target installment's own policy,
    never from a single resolved 'broker's tenant' -- must resolve correctly
    for either of a broker's two simultaneously-active insurers.
    """
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company_a, company_a_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="M2M Pay Insurer A",
        contact_email=f"a-{uuid.uuid4()}@m2m-pay.example.com",
    )
    company_b, company_b_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="M2M Pay Insurer B",
        contact_email=f"b-{uuid.uuid4()}@m2m-pay.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="M2M Pay Broker",
        contact_email=f"broker-{uuid.uuid4()}@m2m-pay.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company_a["id"]
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company_b["id"]
    )

    for company, company_headers in (
        (company_a, company_a_headers),
        (company_b, company_b_headers),
    ):
        fake_squad_client.set_payout_account(
            bank_code="000013",
            account_number="0123456789",
            account_name=f"{company['name']} Settlement",
        )
        settlement_resp = await client.post(
            f"/api/v1/insurance-companies/{company['id']}/settlement-account",
            json={"bank_code": "000013", "account_number": "0123456789"},
            headers=company_headers,
        )
        assert settlement_resp.status_code == 200, settlement_resp.text

    policyholder_a = await create_policyholder(
        client, company_a_headers, broker_id=broker["id"], full_name="Pay Client A"
    )
    policy_a = await create_policy(
        client,
        company_a_headers,
        broker_id=broker["id"],
        policyholder_id=policyholder_a["id"],
        reference_number=f"DN-{uuid.uuid4()}",
        premium_amount_kobo=500_000,
        start_date=date.today().isoformat(),
    )
    policyholder_b = await create_policyholder(
        client, company_b_headers, broker_id=broker["id"], full_name="Pay Client B"
    )
    policy_b = await create_policy(
        client,
        company_b_headers,
        broker_id=broker["id"],
        policyholder_id=policyholder_b["id"],
        reference_number=f"DN-{uuid.uuid4()}",
        premium_amount_kobo=300_000,
        start_date=date.today().isoformat(),
    )

    installment_a_id = (
        await client.get(f"/api/v1/policies/{policy_a['id']}/installments", headers=broker_headers)
    ).json()[0]["id"]
    installment_b_id = (
        await client.get(f"/api/v1/policies/{policy_b['id']}/installments", headers=broker_headers)
    ).json()[0]["id"]

    pay_a_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": installment_a_id},
        headers={**broker_headers, "Idempotency-Key": "m2m-pay-a"},
    )
    assert pay_a_resp.status_code == 201, pay_a_resp.text
    payment_a = pay_a_resp.json()
    assert payment_a["insurance_company_id"] == company_a["id"]

    pay_b_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": installment_b_id},
        headers={**broker_headers, "Idempotency-Key": "m2m-pay-b"},
    )
    assert pay_b_resp.status_code == 201, pay_b_resp.text
    payment_b = pay_b_resp.json()
    assert payment_b["insurance_company_id"] == company_b["id"]
    # Same broker, two different insurers, both resolved correctly from each
    # installment's own policy -- not from a single "broker's tenant".
    assert payment_a["insurance_company_id"] != payment_b["insurance_company_id"]


async def test_bulk_payment_rejects_a_batch_spanning_two_insurers(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """Confirms the single-insurer-per-batch rule (docs/adr/0011): bulk
    payments still settle as exactly one payout, so a batch mixing
    installments from two different insurers must be rejected outright.
    """
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company_a, company_a_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="M2M Bulk Insurer A",
        contact_email=f"a-{uuid.uuid4()}@m2m-bulk.example.com",
    )
    company_b, company_b_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="M2M Bulk Insurer B",
        contact_email=f"b-{uuid.uuid4()}@m2m-bulk.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="M2M Bulk Broker",
        contact_email=f"broker-{uuid.uuid4()}@m2m-bulk.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company_a["id"]
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company_b["id"]
    )

    policyholder_a = await create_policyholder(
        client, company_a_headers, broker_id=broker["id"], full_name="Bulk Client A"
    )
    policy_a = await create_policy(
        client,
        company_a_headers,
        broker_id=broker["id"],
        policyholder_id=policyholder_a["id"],
        reference_number=f"DN-{uuid.uuid4()}",
        start_date=date.today().isoformat(),
    )
    policyholder_b = await create_policyholder(
        client, company_b_headers, broker_id=broker["id"], full_name="Bulk Client B"
    )
    policy_b = await create_policy(
        client,
        company_b_headers,
        broker_id=broker["id"],
        policyholder_id=policyholder_b["id"],
        reference_number=f"DN-{uuid.uuid4()}",
        start_date=date.today().isoformat(),
    )

    installment_a_id = (
        await client.get(f"/api/v1/policies/{policy_a['id']}/installments", headers=broker_headers)
    ).json()[0]["id"]
    installment_b_id = (
        await client.get(f"/api/v1/policies/{policy_b['id']}/installments", headers=broker_headers)
    ).json()[0]["id"]

    # Exactly 1 VA exists already -- created at broker approval, not during
    # payment -- so the assertion below is "unchanged", not "still zero".
    va_count_before = len(fake_squad_client.created_accounts)
    resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": [installment_a_id, installment_b_id]},
        headers={**broker_headers, "Idempotency-Key": "m2m-bulk-mixed"},
    )
    assert resp.status_code == 422, resp.text
    assert len(fake_squad_client.created_accounts) == va_count_before
