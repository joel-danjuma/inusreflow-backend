import uuid
from datetime import UTC, date, datetime
from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.integrations.squad.signature import compute_static_va_signature
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


async def test_broker_dashboard_summary_reflects_successful_payment_and_commission(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Dashboard Summary Insurance",
        contact_email=f"admin-{uuid.uuid4()}@dashboard-summary-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Dashboard Summary Brokers",
        contact_email=f"admin-{uuid.uuid4()}@dashboard-summary-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )

    # Global default has broker_rate_bps=NULL (zero broker commission) -- set
    # an explicit broker-scoped rate so total_commission_kobo is nonzero.
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
        bank_code="000013", account_number="0123456789", account_name="Dashboard Summary Insurance"
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
        name="Dash Payer",
        premium_amount_kobo=500_000,
    )
    installments_resp = await client.get(
        f"/api/v1/policies/{policy['id']}/installments", headers=broker_headers
    )
    installment_id = installments_resp.json()[0]["id"]

    create_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": installment_id},
        headers={**broker_headers, "Idempotency-Key": "dash-summary-key-1"},
    )
    assert create_resp.status_code == 201, create_resp.text
    payment = create_resp.json()

    squad_tx_ref = str(uuid.uuid4())
    fake_squad_client.simulate_transaction(squad_tx_ref, status="SUCCESS")
    webhook_payload, webhook_headers = _build_sva_webhook(
        squad_tx_ref=squad_tx_ref,
        va_number=payment["squad_virtual_account_number"],
        amount_kobo=500_000,
        broker_id=broker["id"],
    )
    webhook_resp = await client.post(
        "/api/v1/webhooks/squad", json=webhook_payload, headers=webhook_headers
    )
    assert webhook_resp.status_code == 200, webhook_resp.text

    summary_resp = await client.get("/api/v1/brokers/me/dashboard-summary", headers=broker_headers)
    assert summary_resp.status_code == 200, summary_resp.text
    summary = summary_resp.json()

    assert summary["total_premiums_collected_kobo"] == 500_000
    assert summary["total_premiums_this_month_kobo"] == 500_000
    assert summary["total_commission_kobo"] > 0
    assert summary["client_retention_rate"] == 100.0
    assert summary["active_clients_count"] == 1
    assert len(summary["monthly_trends"]) == 6
    current_month_key = datetime.now(UTC).strftime("%Y-%m")
    current_bucket = next(p for p in summary["monthly_trends"] if p["month"] == current_month_key)
    assert current_bucket["amount_kobo"] == 500_000
    assert summary["monthly_trends"][-1]["month"] == current_month_key


async def test_broker_dashboard_summary_forbidden_for_non_broker_roles(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    _, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Dashboard Forbidden Insurance",
        contact_email=f"admin-{uuid.uuid4()}@dashboard-forbidden-insurance.example.com",
    )

    summary_resp = await client.get("/api/v1/brokers/me/dashboard-summary", headers=company_headers)
    assert summary_resp.status_code == 403, summary_resp.text

    portfolio_resp = await client.get("/api/v1/brokers/me/portfolio", headers=company_headers)
    assert portfolio_resp.status_code == 403, portfolio_resp.text

    admin_summary_resp = await client.get(
        "/api/v1/brokers/me/dashboard-summary", headers=admin_headers
    )
    assert admin_summary_resp.status_code == 403, admin_summary_resp.text


async def test_broker_portfolio_pagination_and_next_payment_advances_after_payment(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Portfolio Insurance",
        contact_email=f"admin-{uuid.uuid4()}@portfolio-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Portfolio Brokers",
        contact_email=f"admin-{uuid.uuid4()}@portfolio-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )
    fake_squad_client.set_payout_account(
        bank_code="000013", account_number="0123456789", account_name="Portfolio Insurance"
    )
    settlement_resp = await client.post(
        f"/api/v1/insurance-companies/{company['id']}/settlement-account",
        json={"bank_code": "000013", "account_number": "0123456789"},
        headers=company_headers,
    )
    assert settlement_resp.status_code == 200, settlement_resp.text

    policies = [
        await _create_policyholder_and_policy(
            client,
            company_headers,
            broker_id=broker["id"],
            name=f"Portfolio Client {i}",
            premium_amount_kobo=100_000,
        )
        for i in range(3)
    ]

    page1_resp = await client.get(
        "/api/v1/brokers/me/portfolio",
        headers=broker_headers,
        params={"page": 1, "per_page": 2},
    )
    assert page1_resp.status_code == 200, page1_resp.text
    page1 = page1_resp.json()
    assert page1["total"] == 3
    assert page1["page"] == 1
    assert page1["per_page"] == 2
    assert len(page1["items"]) == 2

    page2_resp = await client.get(
        "/api/v1/brokers/me/portfolio",
        headers=broker_headers,
        params={"page": 2, "per_page": 2},
    )
    assert page2_resp.status_code == 200, page2_resp.text
    page2 = page2_resp.json()
    assert len(page2["items"]) == 1

    all_client_names = {item["client_name"] for item in (*page1["items"], *page2["items"])}
    assert all_client_names == {f"Portfolio Client {i}" for i in range(3)}
    first_item = page1["items"][0]
    assert first_item["payment_status"] == "due"
    assert first_item["next_installment_id"] is not None
    assert first_item["next_payment_date"] is not None
    assert first_item["policy_status"] == "active"
    assert first_item["premium_amount_kobo"] == 100_000

    target_policy = policies[0]
    installments_resp = await client.get(
        f"/api/v1/policies/{target_policy['id']}/installments", headers=broker_headers
    )
    installments = sorted(installments_resp.json(), key=lambda i: i["due_date"])
    first_installment, second_installment = installments[0], installments[1]

    create_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": first_installment["id"]},
        headers={**broker_headers, "Idempotency-Key": "portfolio-pay-key-1"},
    )
    assert create_resp.status_code == 201, create_resp.text
    payment = create_resp.json()
    squad_tx_ref = str(uuid.uuid4())
    fake_squad_client.simulate_transaction(squad_tx_ref, status="SUCCESS")
    webhook_payload, webhook_headers = _build_sva_webhook(
        squad_tx_ref=squad_tx_ref,
        va_number=payment["squad_virtual_account_number"],
        amount_kobo=100_000,
        broker_id=broker["id"],
    )
    webhook_resp = await client.post(
        "/api/v1/webhooks/squad", json=webhook_payload, headers=webhook_headers
    )
    assert webhook_resp.status_code == 200, webhook_resp.text

    full_resp = await client.get(
        "/api/v1/brokers/me/portfolio",
        headers=broker_headers,
        params={"page": 1, "per_page": 10},
    )
    assert full_resp.status_code == 200, full_resp.text
    updated_item = next(
        item for item in full_resp.json()["items"] if item["policy_id"] == target_policy["id"]
    )
    # The 12-installment rolling window (policy_service.INSTALLMENT_WINDOW_SIZE)
    # means paying the earliest installment advances "next payment" to the
    # second-earliest due date rather than clearing it to "paid".
    assert updated_item["payment_status"] == "due"
    assert updated_item["next_installment_id"] == second_installment["id"]


async def test_portfolio_hides_pay_now_when_a_payment_is_already_in_flight(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """initiate_payment (payment_service.py) rejects a second attempt on an
    installment that already has an 'initiated' Payment -- the portfolio
    endpoint must never advertise Pay Now for one of these, or the broker
    hits a raw 409 with no explanation (the bug this test guards against).
    """
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="In Flight Insurance",
        contact_email=f"admin-{uuid.uuid4()}@in-flight-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="In Flight Brokers",
        contact_email=f"admin-{uuid.uuid4()}@in-flight-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )

    policy = await _create_policyholder_and_policy(
        client,
        company_headers,
        broker_id=broker["id"],
        name="In Flight Client",
        premium_amount_kobo=100_000,
    )
    installments_resp = await client.get(
        f"/api/v1/policies/{policy['id']}/installments", headers=broker_headers
    )
    first_installment_id = installments_resp.json()[0]["id"]

    create_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": first_installment_id},
        headers={**broker_headers, "Idempotency-Key": "in-flight-key-1"},
    )
    assert create_resp.status_code == 201, create_resp.text
    assert create_resp.json()["status"] == "initiated"

    portfolio_resp = await client.get(
        "/api/v1/brokers/me/portfolio",
        headers=broker_headers,
        params={"page": 1, "per_page": 10},
    )
    assert portfolio_resp.status_code == 200, portfolio_resp.text
    item = next(row for row in portfolio_resp.json()["items"] if row["policy_id"] == policy["id"])
    assert item["payment_status"] == "in_progress"
    assert item["next_installment_id"] is None

    # Confirms the guard is real, not just cosmetic: attempting to pay the
    # same installment again (as the old UI would have let a broker do)
    # still 409s exactly as before.
    retry_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": first_installment_id},
        headers={**broker_headers, "Idempotency-Key": "in-flight-key-2"},
    )
    assert retry_resp.status_code == 409, retry_resp.text


async def test_portfolio_includes_reference_number(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Portfolio Reference Insurance",
        contact_email=f"admin-{uuid.uuid4()}@portfolio-reference-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Portfolio Reference Brokers",
        contact_email=f"admin-{uuid.uuid4()}@portfolio-reference-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )
    policy = await _create_policyholder_and_policy(
        client,
        company_headers,
        broker_id=broker["id"],
        name="Portfolio Reference Client",
        premium_amount_kobo=100_000,
    )
    installments_resp = await client.get(
        f"/api/v1/policies/{policy['id']}/installments", headers=broker_headers
    )
    installment_id = installments_resp.json()[0]["id"]

    portfolio_before = await client.get(
        "/api/v1/brokers/me/portfolio", headers=broker_headers, params={"page": 1, "per_page": 10}
    )
    item_before = next(
        row for row in portfolio_before.json()["items"] if row["policy_id"] == policy["id"]
    )
    assert item_before["next_payment_reference_number"] is None

    set_resp = await client.patch(
        f"/api/v1/installments/{installment_id}/reference-number",
        json={"reference_number": "DN-PORTFOLIO-1"},
        headers=broker_headers,
    )
    assert set_resp.status_code == 200, set_resp.text

    portfolio_after = await client.get(
        "/api/v1/brokers/me/portfolio", headers=broker_headers, params={"page": 1, "per_page": 10}
    )
    item_after = next(
        row for row in portfolio_after.json()["items"] if row["policy_id"] == policy["id"]
    )
    assert item_after["next_payment_reference_number"] == "DN-PORTFOLIO-1"
