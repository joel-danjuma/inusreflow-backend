import uuid
from datetime import date
from typing import Any

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.integrations.squad.signature import compute_static_va_signature
from app.models.settlement_payout import SettlementPayout
from tests.fakes import FakeSquadClient
from tests.helpers import (
    assign_broker_to_insurer,
    create_policy,
    create_policyholder,
    onboard_and_approve_broker,
    onboard_and_approve_insurance_company,
    seed_and_activate_insureflow_admin,
)

_BANK_CODE = "000013"  # GTBank NIP code, not the classic CBN code
_ACCOUNT_NUMBER = "0123456789"


def _build_sva_webhook(
    *,
    squad_tx_ref: str,
    va_number: str,
    amount_kobo: int,
    broker_id: str,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Returns (payload, headers) for a correctly-signed SVA webhook.

    squad_tx_ref: Squad's own transaction_reference UUID (distinct from our
                  internal squad_transaction_ref on the Payment row).
    broker_id:    broker UUID as string — used as customer_identifier (matches
                  what onboarding_service sets when creating the Business SVA).
    """
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


async def _setup_payable_installment(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> tuple[dict, dict[str, str], dict, dict[str, str], str, str]:
    """Onboards an approved+assigned insurer/broker pair, confirms the
    insurer's settlement account, and creates a policy with a due
    installment. Returns (company, company_headers, broker, broker_headers,
    policy_id, installment_id).

    broker is returned so callers have the broker id for building SVA webhook
    customer_identifier (= str(broker.id) by VA creation convention).
    """
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)

    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Payment Flow Insurance",
        contact_email=f"admin-{uuid.uuid4()}@payment-flow-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Payment Flow Brokers",
        contact_email=f"admin-{uuid.uuid4()}@payment-flow-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )

    fake_squad_client.set_payout_account(
        bank_code=_BANK_CODE,
        account_number=_ACCOUNT_NUMBER,
        account_name="Payment Flow Insurance Settlement",
    )
    settlement_resp = await client.post(
        f"/api/v1/insurance-companies/{company['id']}/settlement-account",
        json={"bank_code": _BANK_CODE, "account_number": _ACCOUNT_NUMBER},
        headers=company_headers,
    )
    assert settlement_resp.status_code == 200, settlement_resp.text
    assert settlement_resp.json()["settlement_account_name"] == "Payment Flow Insurance Settlement"

    policyholder = await create_policyholder(
        client,
        company_headers,
        broker_id=broker["id"],
        full_name="Pay Payer",
        email="pay.payer@example.com",
    )

    policy = await create_policy(
        client,
        company_headers,
        broker_id=broker["id"],
        policyholder_id=policyholder["id"],
        reference_number=f"DN-{uuid.uuid4()}",
        premium_amount_kobo=500_000,
        start_date=date.today().isoformat(),
    )

    installments_resp = await client.get(
        f"/api/v1/policies/{policy['id']}/installments", headers=broker_headers
    )
    installments = installments_resp.json()
    installment_id = installments[0]["id"]

    return company, company_headers, broker, broker_headers, policy["id"], installment_id


async def test_single_payment_success_settles_and_marks_installment_paid(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    (
        company,
        _,
        broker,
        broker_headers,
        policy_id,
        installment_id,
    ) = await _setup_payable_installment(client, db_session, fake_squad_client)

    create_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": installment_id},
        headers={**broker_headers, "Idempotency-Key": "pay-key-1"},
    )
    assert create_resp.status_code == 201, create_resp.text
    payment = create_resp.json()
    assert payment["status"] == "initiated"
    va_number = payment["squad_virtual_account_number"]
    assert va_number

    # Replaying the same Idempotency-Key must not create another payment.
    replay_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": installment_id},
        headers={**broker_headers, "Idempotency-Key": "pay-key-1"},
    )
    assert replay_resp.status_code == 201, replay_resp.text
    assert replay_resp.json()["id"] == payment["id"]
    # Only 1 VA should exist -- created at broker approval, not during payment.
    assert len(fake_squad_client.created_accounts) == 1

    # Squad fires an SVA webhook when the customer transfers funds to the VA.
    squad_tx_ref = str(uuid.uuid4())
    fake_squad_client.simulate_transaction(squad_tx_ref, status="SUCCESS")
    webhook_payload, webhook_headers = _build_sva_webhook(
        squad_tx_ref=squad_tx_ref,
        va_number=va_number,
        amount_kobo=500_000,
        broker_id=broker["id"],
    )
    webhook_resp = await client.post(
        "/api/v1/webhooks/squad", json=webhook_payload, headers=webhook_headers
    )
    assert webhook_resp.status_code == 200, webhook_resp.text

    get_resp = await client.get(f"/api/v1/payments/{payment['id']}", headers=broker_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "success"

    installments_resp = await client.get(
        f"/api/v1/policies/{policy_id}/installments", headers=broker_headers
    )
    paid_installment = next(i for i in installments_resp.json() if i["id"] == installment_id)
    assert paid_installment["status"] == "paid"

    payout = await db_session.scalar(
        select(SettlementPayout).where(
            SettlementPayout.insurance_company_id == uuid.UUID(company["id"])
        )
    )
    assert payout is not None
    assert payout.status == "success"
    assert len(fake_squad_client.transfers) == 1

    # A duplicate webhook delivery (Squad's own retry) must be a no-op.
    duplicate_resp = await client.post(
        "/api/v1/webhooks/squad", json=webhook_payload, headers=webhook_headers
    )
    assert duplicate_resp.status_code == 200
    assert len(fake_squad_client.transfers) == 1


async def test_single_payment_failure_never_settles_or_marks_installment_paid(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """A Squad verify_transaction response with non-SUCCESS status results in
    payment.status='failed' (SVA has no MISMATCH/EXPIRED concepts) and
    triggers neither a settlement transfer nor an installment state change.
    """
    (
        company,
        _,
        broker,
        broker_headers,
        _policy_id,
        installment_id,
    ) = await _setup_payable_installment(client, db_session, fake_squad_client)

    create_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": installment_id},
        headers={**broker_headers, "Idempotency-Key": "pay-key-2"},
    )
    assert create_resp.status_code == 201, create_resp.text
    payment = create_resp.json()
    va_number = payment["squad_virtual_account_number"]

    squad_tx_ref = str(uuid.uuid4())
    fake_squad_client.simulate_transaction(squad_tx_ref, status="FAILED")
    webhook_payload, webhook_headers = _build_sva_webhook(
        squad_tx_ref=squad_tx_ref,
        va_number=va_number,
        amount_kobo=500_000,
        broker_id=broker["id"],
    )
    webhook_resp = await client.post(
        "/api/v1/webhooks/squad", json=webhook_payload, headers=webhook_headers
    )
    assert webhook_resp.status_code == 200, webhook_resp.text

    get_resp = await client.get(f"/api/v1/payments/{payment['id']}", headers=broker_headers)
    assert get_resp.json()["status"] == "failed"

    payout = await db_session.scalar(
        select(SettlementPayout).where(
            SettlementPayout.insurance_company_id == uuid.UUID(company["id"])
        )
    )
    assert payout is None
    assert fake_squad_client.transfers == []


async def test_list_settlements_is_scoped_and_broker_forbidden(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)

    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Settlement List Insurance",
        contact_email=f"admin-{uuid.uuid4()}@settlement-list-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Settlement List Brokers",
        contact_email=f"admin-{uuid.uuid4()}@settlement-list-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )
    fake_squad_client.set_payout_account(
        bank_code=_BANK_CODE,
        account_number=_ACCOUNT_NUMBER,
        account_name="Settlement List Insurance Settlement",
    )
    settlement_resp = await client.post(
        f"/api/v1/insurance-companies/{company['id']}/settlement-account",
        json={"bank_code": _BANK_CODE, "account_number": _ACCOUNT_NUMBER},
        headers=company_headers,
    )
    assert settlement_resp.status_code == 200, settlement_resp.text

    policyholder = await create_policyholder(
        client,
        company_headers,
        broker_id=broker["id"],
        full_name="Settlement List Payer",
        email="settlement.list@example.com",
    )
    policy = await create_policy(
        client,
        company_headers,
        broker_id=broker["id"],
        policyholder_id=policyholder["id"],
        reference_number=f"DN-{uuid.uuid4()}",
        premium_amount_kobo=500_000,
        start_date=date.today().isoformat(),
    )
    installments_resp = await client.get(
        f"/api/v1/policies/{policy['id']}/installments", headers=broker_headers
    )
    installment_id = installments_resp.json()[0]["id"]

    create_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": installment_id},
        headers={**broker_headers, "Idempotency-Key": "settlement-list-key"},
    )
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

    insurer_list = await client.get("/api/v1/settlements", headers=company_headers)
    assert insurer_list.status_code == 200, insurer_list.text
    assert len(insurer_list.json()) == 1
    assert insurer_list.json()[0]["insurance_company_id"] == company["id"]

    admin_list = await client.get(
        "/api/v1/settlements", headers=admin_headers, params={"status": "success"}
    )
    assert admin_list.status_code == 200, admin_list.text
    assert any(s["insurance_company_id"] == company["id"] for s in admin_list.json())

    broker_forbidden = await client.get("/api/v1/settlements", headers=broker_headers)
    assert broker_forbidden.status_code == 403, broker_forbidden.text

    payout_id = insurer_list.json()[0]["id"]
    detail_resp = await client.get(f"/api/v1/settlements/{payout_id}", headers=company_headers)
    assert detail_resp.status_code == 200, detail_resp.text
    assert detail_resp.json()["id"] == payout_id

    admin_detail_resp = await client.get(f"/api/v1/settlements/{payout_id}", headers=admin_headers)
    assert admin_detail_resp.status_code == 200, admin_detail_resp.text

    broker_detail_forbidden = await client.get(
        f"/api/v1/settlements/{payout_id}", headers=broker_headers
    )
    assert broker_detail_forbidden.status_code == 403, broker_detail_forbidden.text


async def test_list_payments_is_scoped_by_role(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """A broker only ever sees its own broker's payments (even if it passes
    another broker's id), an Insurance Company Admin sees every payment
    under its tenant, and an Insureflow Admin sees everything.
    """
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)

    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="List Payments Insurance",
        contact_email=f"admin-{uuid.uuid4()}@list-payments-insurance.example.com",
    )
    broker_a, broker_a_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="List Payments Broker A",
        contact_email=f"admin-{uuid.uuid4()}@list-payments-broker-a.example.com",
    )
    broker_b, broker_b_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="List Payments Broker B",
        contact_email=f"admin-{uuid.uuid4()}@list-payments-broker-b.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker_a["id"], insurance_company_id=company["id"]
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker_b["id"], insurance_company_id=company["id"]
    )

    async def _create_payment(broker_id: str, broker_headers: dict[str, str], idem_key: str) -> str:
        policyholder = await create_policyholder(
            client,
            company_headers,
            broker_id=broker_id,
            full_name="List Payer",
            email=f"{uuid.uuid4()}@example.com",
        )
        policy = await create_policy(
            client,
            company_headers,
            broker_id=broker_id,
            policyholder_id=policyholder["id"],
            reference_number=f"DN-{uuid.uuid4()}",
            premium_amount_kobo=100_000,
            start_date=date.today().isoformat(),
        )
        installments_resp = await client.get(
            f"/api/v1/policies/{policy['id']}/installments", headers=broker_headers
        )
        installment_id = installments_resp.json()[0]["id"]
        pay_resp = await client.post(
            "/api/v1/payments",
            json={"installment_id": installment_id},
            headers={**broker_headers, "Idempotency-Key": idem_key},
        )
        assert pay_resp.status_code == 201, pay_resp.text
        return str(pay_resp.json()["id"])

    payment_a_id = await _create_payment(broker_a["id"], broker_a_headers, "list-key-a")
    payment_b_id = await _create_payment(broker_b["id"], broker_b_headers, "list-key-b")

    broker_a_list = await client.get(
        "/api/v1/payments", headers=broker_a_headers, params={"broker_id": broker_b["id"]}
    )
    assert broker_a_list.status_code == 200, broker_a_list.text
    broker_a_ids = {p["id"] for p in broker_a_list.json()}
    assert broker_a_ids == {payment_a_id}

    insurer_list = await client.get("/api/v1/payments", headers=company_headers)
    assert insurer_list.status_code == 200, insurer_list.text
    insurer_ids = {p["id"] for p in insurer_list.json()}
    assert insurer_ids == {payment_a_id, payment_b_id}

    admin_list = await client.get(
        "/api/v1/payments", headers=admin_headers, params={"broker_id": broker_b["id"]}
    )
    assert admin_list.status_code == 200, admin_list.text
    assert {p["id"] for p in admin_list.json()} == {payment_b_id}


async def test_webhook_with_invalid_signature_is_rejected_and_never_processed(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    _, _, broker, broker_headers, _policy_id, installment_id = await _setup_payable_installment(
        client, db_session, fake_squad_client
    )

    create_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": installment_id},
        headers={**broker_headers, "Idempotency-Key": "pay-key-3"},
    )
    payment = create_resp.json()
    va_number = payment["squad_virtual_account_number"]

    squad_tx_ref = str(uuid.uuid4())
    fake_squad_client.simulate_transaction(squad_tx_ref, status="SUCCESS")
    webhook_payload, _ = _build_sva_webhook(
        squad_tx_ref=squad_tx_ref,
        va_number=va_number,
        amount_kobo=500_000,
        broker_id=broker["id"],
    )
    webhook_resp = await client.post(
        "/api/v1/webhooks/squad",
        json=webhook_payload,
        headers={"x-squad-signature": "not-a-real-signature"},
    )
    assert webhook_resp.status_code == 200

    get_resp = await client.get(f"/api/v1/payments/{payment['id']}", headers=broker_headers)
    assert get_resp.json()["status"] == "initiated"
    assert fake_squad_client.transfers == []
