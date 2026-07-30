import uuid
from datetime import date, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.premium_installment import PremiumInstallment
from app.services import installment_service, reminder_service
from tests.fakes import FakeSquadClient
from tests.helpers import (
    assign_broker_to_insurer,
    create_policy,
    create_policyholder,
    onboard_and_approve_broker,
    onboard_and_approve_insurance_company,
    seed_and_activate_insureflow_admin,
)


async def test_create_policy_installments_overdue_flip_reminder_sent(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)

    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Lifecycle Insurance",
        contact_email="admin@lifecycle-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Lifecycle Brokers",
        contact_email="admin@lifecycle-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )

    policyholder = await create_policyholder(
        client,
        company_headers,
        broker_id=broker["id"],
        full_name="Jane Doe",
        email="jane@example.com",
    )

    policy = await create_policy(
        client,
        company_headers,
        broker_id=broker["id"],
        policyholder_id=policyholder["id"],
        reference_number="DN-LIFECYCLE-0001",
        start_date=date.today().isoformat(),
    )
    assert policy["status"] == "active"

    installments_resp = await client.get(
        f"/api/v1/policies/{policy['id']}/installments", headers=broker_headers
    )
    assert installments_resp.status_code == 200
    installments = installments_resp.json()
    assert len(installments) == 12
    assert all(i["status"] == "due" for i in installments)

    first_installment_id = installments[0]["id"]
    db_installment = await db_session.get(PremiumInstallment, uuid.UUID(first_installment_id))
    assert db_installment is not None
    db_installment.due_date = date.today() - timedelta(days=1)
    await db_session.flush()

    # >=1, not ==1: flag_overdue_installments scans every due installment in
    # the database, not just this test's -- other already-overdue rows may
    # coexist (e.g. tests/load/ seed data, or other tests' fixtures sharing
    # this DB). The precise per-installment check below is what actually
    # proves this test's installment was flagged.
    flagged_count = await installment_service.flag_overdue_installments(db_session)
    assert flagged_count >= 1

    installments_resp_2 = await client.get(
        f"/api/v1/policies/{policy['id']}/installments", headers=broker_headers
    )
    refreshed = installments_resp_2.json()
    refreshed_first = next(i for i in refreshed if i["id"] == first_installment_id)
    assert refreshed_first["status"] == "overdue"

    reminder_resp = await client.post(
        "/api/v1/reminders",
        json={"installment_id": first_installment_id},
        headers=company_headers,
    )
    assert reminder_resp.status_code == 201, reminder_resp.text
    reminder = reminder_resp.json()
    assert reminder["status"] == "queued"

    await reminder_service.mark_reminder_sent(db_session, reminder_id=uuid.UUID(reminder["id"]))

    reminders_resp = await client.get(
        "/api/v1/reminders", params={"broker_id": broker["id"]}, headers=company_headers
    )
    assert reminders_resp.status_code == 200
    sent_reminder = next(r for r in reminders_resp.json() if r["id"] == reminder["id"])
    assert sent_reminder["status"] == "sent"
    assert sent_reminder["sent_at"] is not None


async def test_create_policy_with_optional_detail_fields(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)

    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Detail Fields Insurance",
        contact_email="admin@detail-fields-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Detail Fields Brokers",
        contact_email="admin@detail-fields-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )

    policyholder = await create_policyholder(
        client,
        company_headers,
        broker_id=broker["id"],
        full_name="John Roe",
        email="john@example.com",
    )

    policy = await create_policy(
        client,
        company_headers,
        broker_id=broker["id"],
        policyholder_id=policyholder["id"],
        reference_number="DN-DETAIL-0001",
        start_date=date.today().isoformat(),
        policy_name="John Roe -- Comprehensive Auto",
        duration_months=24,
        coverage_amount_kobo=50_000_000,
        coverage_items="Vehicle, third-party liability",
        beneficiaries="John Roe",
        broker_notes="VIP client",
        internal_tags="vip, renewal-2027",
    )
    assert policy["policy_name"] == "John Roe -- Comprehensive Auto"
    assert policy["duration_months"] == 24
    assert policy["coverage_amount_kobo"] == 50_000_000
    assert policy["coverage_items"] == "Vehicle, third-party liability"
    assert policy["beneficiaries"] == "John Roe"
    assert policy["broker_notes"] == "VIP client"
    assert policy["internal_tags"] == "vip, renewal-2027"

    # Omitting every optional detail field still works and defaults to null --
    # duration_months in particular must never affect installment generation
    # (no expiry/renewal concept exists yet).
    policy_2 = await create_policy(
        client,
        company_headers,
        broker_id=broker["id"],
        policyholder_id=policyholder["id"],
        reference_number="DN-DETAIL-0002",
        premium_amount_kobo=300_000,
        start_date=date.today().isoformat(),
    )
    assert policy_2["policy_name"] is None
    assert policy_2["duration_months"] is None
    assert policy_2["coverage_amount_kobo"] is None

    installments_resp = await client.get(
        f"/api/v1/policies/{policy_2['id']}/installments", headers=broker_headers
    )
    assert len(installments_resp.json()) == 12
