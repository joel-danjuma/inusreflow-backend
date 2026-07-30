import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.integrations.squad.signature import compute_static_va_signature
from app.models.premium_installment import PremiumInstallment
from app.services import installment_service
from tests.fakes import FakeSquadClient
from tests.helpers import (
    assign_broker_to_insurer,
    create_policy,
    create_policyholder,
    onboard_and_approve_broker,
    onboard_and_approve_insurance_company,
    seed_and_activate_insureflow_admin,
)


def _build_sva_webhook(
    *, squad_tx_ref: str, va_number: str, amount_kobo: int, broker_id: str
) -> tuple[dict[str, Any], dict[str, str]]:
    amount_str = str(amount_kobo)
    currency = "NGN"
    signature = compute_static_va_signature(
        secret_key=get_settings().squad_secret_key,
        transaction_reference=squad_tx_ref,
        virtual_account_number=va_number,
        currency=currency,
        principal_amount=amount_str,
        settled_amount=amount_str,
        customer_identifier=broker_id,
    )
    payload: dict[str, Any] = {
        "transaction_reference": squad_tx_ref,
        "virtual_account_number": va_number,
        "principal_amount": amount_str,
        "settled_amount": amount_str,
        "customer_identifier": broker_id,
        "transaction_type": "static_virtual_account",
        "currency": currency,
    }
    return payload, {"x-squad-signature": signature}


async def _create_policyholder_and_policy(
    client: AsyncClient,
    company_headers: dict[str, str],
    *,
    broker_id: str,
    name: str,
    premium_amount_kobo: int,
) -> dict[str, Any]:
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
        premium_amount_kobo=premium_amount_kobo,
        start_date=date.today().isoformat(),
    )


async def test_insurer_dashboard_summary_and_recent_policies(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Insurer Dashboard Insurance",
        contact_email=f"admin-{uuid.uuid4()}@insurer-dashboard-insurance.example.com",
    )
    broker_a, broker_a_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Insurer Dashboard Broker A",
        contact_email=f"admin-{uuid.uuid4()}@insurer-dashboard-broker-a.example.com",
    )
    broker_b, _ = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Insurer Dashboard Broker B",
        contact_email=f"admin-{uuid.uuid4()}@insurer-dashboard-broker-b.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker_a["id"], insurance_company_id=company["id"]
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker_b["id"], insurance_company_id=company["id"]
    )

    policy_1 = await _create_policyholder_and_policy(
        client,
        company_headers,
        broker_id=broker_a["id"],
        name="Recent Client One",
        premium_amount_kobo=200_000,
    )
    policy_2 = await _create_policyholder_and_policy(
        client,
        company_headers,
        broker_id=broker_a["id"],
        name="Recent Client Two",
        premium_amount_kobo=300_000,
    )

    summary_resp = await client.get(
        "/api/v1/insurance-companies/me/dashboard-summary", headers=company_headers
    )
    assert summary_resp.status_code == 200, summary_resp.text
    summary = summary_resp.json()
    assert summary["new_policies_count"] >= 2
    assert summary["total_brokers_count"] == 2
    # Every fresh installment starts "due" -- both new policies' full 12-item
    # windows are immediately outstanding.
    assert summary["outstanding_premiums_kobo"] >= 200_000 * 12 + 300_000 * 12

    recent_resp = await client.get(
        "/api/v1/insurance-companies/me/recent-policies", headers=company_headers
    )
    assert recent_resp.status_code == 200, recent_resp.text
    recent = recent_resp.json()
    recent_ids = {item["policy_id"] for item in recent}
    assert policy_1["id"] in recent_ids
    assert policy_2["id"] in recent_ids
    match = next(item for item in recent if item["policy_id"] == policy_2["id"])
    assert match["customer_name"] == "Recent Client Two"
    assert match["broker_name"] == "Insurer Dashboard Broker A"
    assert match["policy_amount_kobo"] == 300_000
    assert match["policy_number"].startswith("POL-")


async def test_insurer_dashboard_forbidden_for_non_insurer_roles(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    _, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Insurer Dashboard Forbidden Brokers",
        contact_email=f"admin-{uuid.uuid4()}@insurer-dashboard-forbidden-brokers.example.com",
    )

    for path in (
        "dashboard-summary",
        "outstanding-policies",
        "recent-policies",
        "broker-performance",
        "latest-payments",
    ):
        resp = await client.get(f"/api/v1/insurance-companies/me/{path}", headers=broker_headers)
        assert resp.status_code == 403, (path, resp.text)
        admin_resp = await client.get(
            f"/api/v1/insurance-companies/me/{path}", headers=admin_headers
        )
        assert admin_resp.status_code == 403, (path, admin_resp.text)


async def test_outstanding_policies_and_bulk_reminders(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Outstanding Insurance",
        contact_email=f"admin-{uuid.uuid4()}@outstanding-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Outstanding Brokers",
        contact_email=f"admin-{uuid.uuid4()}@outstanding-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )

    policy = await _create_policyholder_and_policy(
        client,
        company_headers,
        broker_id=broker["id"],
        name="Overdue Customer",
        premium_amount_kobo=150_000,
    )
    installments_resp = await client.get(
        f"/api/v1/policies/{policy['id']}/installments", headers=broker_headers
    )
    first_installment_id = installments_resp.json()[0]["id"]

    db_installment = await db_session.get(PremiumInstallment, uuid.UUID(first_installment_id))
    assert db_installment is not None
    # 5 days overdue -- status flips to 'overdue' immediately (unchanged
    # behavior), but this is still within the 30-day grace period, so it
    # must not show up as "actionable" on any insurer-facing surface.
    # Uses UTC (matching the endpoint's own clock reference, datetime.now(UTC))
    # rather than local date.today() -- the two can disagree by a day right
    # around local midnight depending on the machine's timezone.
    db_installment.due_date = datetime.now(UTC).date() - timedelta(days=5)
    await db_session.flush()
    flagged = await installment_service.flag_overdue_installments(db_session)
    assert flagged >= 1

    within_grace_resp = await client.get(
        "/api/v1/insurance-companies/me/outstanding-policies", headers=company_headers
    )
    assert within_grace_resp.status_code == 200, within_grace_resp.text
    assert all(item["policy_id"] != policy["id"] for item in within_grace_resp.json())

    within_grace_summary = await client.get(
        "/api/v1/insurance-companies/me/dashboard-summary", headers=company_headers
    )
    assert within_grace_summary.json()["overdue_policies_count"] == 0

    within_grace_bulk = await client.post("/api/v1/reminders/bulk", headers=company_headers)
    assert within_grace_bulk.status_code == 201, within_grace_bulk.text
    assert within_grace_bulk.json()["reminders_created"] == 0

    # Push it past the grace period: 35 days overdue -> 5 days "actionable"
    # (35 - the 30-day grace period), and now it should surface everywhere.
    db_installment.due_date = datetime.now(UTC).date() - timedelta(days=35)
    await db_session.flush()

    outstanding_resp = await client.get(
        "/api/v1/insurance-companies/me/outstanding-policies", headers=company_headers
    )
    assert outstanding_resp.status_code == 200, outstanding_resp.text
    outstanding = outstanding_resp.json()
    row = next(item for item in outstanding if item["policy_id"] == policy["id"])
    assert row["customer_name"] == "Overdue Customer"
    assert row["broker_name"] == "Outstanding Brokers"
    assert row["premium_amount_kobo"] == 150_000
    assert row["days_overdue"] == 5
    assert row["last_payment_date"] is None
    assert row["reference_number"] is None

    ref_resp = await client.patch(
        f"/api/v1/installments/{first_installment_id}/reference-number",
        json={"reference_number": "DN-OUTSTANDING-1"},
        headers=company_headers,
    )
    assert ref_resp.status_code == 200, ref_resp.text

    outstanding_with_ref = await client.get(
        "/api/v1/insurance-companies/me/outstanding-policies", headers=company_headers
    )
    row_with_ref = next(
        item for item in outstanding_with_ref.json() if item["policy_id"] == policy["id"]
    )
    assert row_with_ref["reference_number"] == "DN-OUTSTANDING-1"

    summary_resp = await client.get(
        "/api/v1/insurance-companies/me/dashboard-summary", headers=company_headers
    )
    assert summary_resp.json()["overdue_policies_count"] >= 1

    bulk_resp = await client.post("/api/v1/reminders/bulk", headers=company_headers)
    assert bulk_resp.status_code == 201, bulk_resp.text
    assert bulk_resp.json()["reminders_created"] >= 1

    reminders_resp = await client.get(
        "/api/v1/reminders", params={"broker_id": broker["id"]}, headers=company_headers
    )
    assert any(r["installment_id"] == first_installment_id for r in reminders_resp.json())

    # A broker calling the insurer-only bulk endpoint must be forbidden.
    broker_bulk_resp = await client.post("/api/v1/reminders/bulk", headers=broker_headers)
    assert broker_bulk_resp.status_code == 403, broker_bulk_resp.text


async def test_broker_performance_and_latest_payments(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Performance Insurance",
        contact_email=f"admin-{uuid.uuid4()}@performance-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Performance Brokers",
        contact_email=f"admin-{uuid.uuid4()}@performance-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )
    config_resp = await client.post(
        "/api/v1/commission-configs",
        json={
            "scope": "broker",
            "gtbank_rate_bps": 50,
            "insureflow_rate_bps": 50,
            "broker_rate_bps": 100,
            "broker_id": broker["id"],
        },
        headers=company_headers,
    )
    assert config_resp.status_code == 201, config_resp.text

    fake_squad_client.set_payout_account(
        bank_code="000013", account_number="0123456789", account_name="Performance Insurance"
    )
    settlement_resp = await client.post(
        f"/api/v1/insurance-companies/{company['id']}/settlement-account",
        json={"bank_code": "000013", "account_number": "0123456789"},
        headers=company_headers,
    )
    assert settlement_resp.status_code == 200, settlement_resp.text

    policy = await _create_policyholder_and_policy(
        client,
        company_headers,
        broker_id=broker["id"],
        name="Performance Payer",
        premium_amount_kobo=400_000,
    )
    installments_resp = await client.get(
        f"/api/v1/policies/{policy['id']}/installments", headers=broker_headers
    )
    installment_id = installments_resp.json()[0]["id"]

    create_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": installment_id},
        headers={**broker_headers, "Idempotency-Key": "perf-key-1"},
    )
    assert create_resp.status_code == 201, create_resp.text
    payment = create_resp.json()

    squad_tx_ref = str(uuid.uuid4())
    fake_squad_client.simulate_transaction(squad_tx_ref, status="SUCCESS")
    webhook_payload, webhook_headers = _build_sva_webhook(
        squad_tx_ref=squad_tx_ref,
        va_number=payment["squad_virtual_account_number"],
        amount_kobo=400_000,
        broker_id=broker["id"],
    )
    webhook_resp = await client.post(
        "/api/v1/webhooks/squad", json=webhook_payload, headers=webhook_headers
    )
    assert webhook_resp.status_code == 200, webhook_resp.text

    performance_resp = await client.get(
        "/api/v1/insurance-companies/me/broker-performance", headers=company_headers
    )
    assert performance_resp.status_code == 200, performance_resp.text
    performance = performance_resp.json()
    row = next(item for item in performance if item["broker_id"] == broker["id"])
    assert row["broker_name"] == "Performance Brokers"
    assert row["policies_sold"] >= 1
    assert row["commission_earned_kobo"] > 0

    payments_resp = await client.get(
        "/api/v1/insurance-companies/me/latest-payments", headers=company_headers
    )
    assert payments_resp.status_code == 200, payments_resp.text
    payments = payments_resp.json()
    match = next(item for item in payments if item["id"] == payment["id"])
    assert match["broker_name"] == "Performance Brokers"
    assert match["total_amount_kobo"] == 400_000
    assert match["policies_paid"] == 1
    assert match["payment_method"] == "Bank Transfer"
    assert match["status"] == "success"
