import uuid
from datetime import date

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.integrations.squad.signature import compute_dynamic_va_signature
from app.models.payment import Payment
from app.models.webhook_event import WebhookEvent
from tests.fakes import FakeSquadClient
from tests.helpers import (
    assign_broker_to_insurer,
    onboard_and_approve_broker,
    onboard_and_approve_insurance_company,
    seed_and_activate_insureflow_admin,
)


async def _setup_in_flight_payment(
    client: AsyncClient, db_session: AsyncSession
) -> tuple[dict[str, str], dict[str, object]]:
    """Onboards an approved+assigned insurer/broker pair and creates one
    in-flight Payment (status='initiated') -- enough to probe webhook
    signature handling without needing the full settlement-account dance
    that tests/e2e/test_single_payment_flow.py sets up, since these tests
    never expect the webhook to reach the success path.
    """
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name=f"Sig Tamper Co {uuid.uuid4()}",
        contact_email=f"admin-{uuid.uuid4()}@sig-tamper.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name=f"Sig Tamper Brokers {uuid.uuid4()}",
        contact_email=f"admin-{uuid.uuid4()}@sig-tamper-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )

    user_resp = await client.post(
        "/api/v1/users",
        json={"full_name": "Sig Tamper Payer", "email": f"{uuid.uuid4()}@example.com"},
        headers=broker_headers,
    )
    assert user_resp.status_code == 201, user_resp.text
    policyholder = user_resp.json()

    policy_resp = await client.post(
        "/api/v1/policies",
        json={
            "policyholder_id": policyholder["id"],
            "premium_amount_kobo": 500_000,
            "premium_frequency": "monthly",
            "start_date": date.today().isoformat(),
        },
        headers=broker_headers,
    )
    assert policy_resp.status_code == 201, policy_resp.text
    policy = policy_resp.json()

    installments_resp = await client.get(
        f"/api/v1/policies/{policy['id']}/installments", headers=broker_headers
    )
    installment_id = installments_resp.json()[0]["id"]

    create_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": installment_id},
        headers={**broker_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert create_resp.status_code == 201, create_resp.text
    return broker_headers, create_resp.json()


async def test_webhook_signature_does_not_cover_a_tampered_amount(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """A genuine signature is only valid for the exact field values it was
    computed over -- an attacker who captures a real signature for one
    amount can't reuse it to claim a different (e.g. lower) amount_received
    was paid, even with transaction_reference/merchant_reference unchanged.
    """
    broker_headers, payment = await _setup_in_flight_payment(client, db_session)
    transaction_ref = payment["squad_transaction_ref"]

    genuine_signature = compute_dynamic_va_signature(
        secret_key=get_settings().squad_secret_key,
        transaction_reference=transaction_ref,
        amount_received="500000",
        merchant_reference=transaction_ref,
    )

    webhook_resp = await client.post(
        "/api/v1/webhooks/squad",
        json={
            "transaction_reference": transaction_ref,
            "amount_received": "1",
            "merchant_reference": transaction_ref,
            "transaction_type": "dynamic_virtual_account",
        },
        headers={"x-squad-encrypted-body": genuine_signature},
    )
    assert webhook_resp.status_code == 200, webhook_resp.text

    get_resp = await client.get(f"/api/v1/payments/{payment['id']}", headers=broker_headers)
    assert get_resp.json()["status"] == "initiated"
    assert fake_squad_client.transfers == []

    event = await db_session.scalar(
        select(WebhookEvent).where(WebhookEvent.transaction_ref == transaction_ref)
    )
    assert event is not None
    assert event.signature_valid is False
    assert event.processing_status == "rejected"


async def test_webhook_signature_does_not_redirect_to_a_different_transaction_reference(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """transaction_reference is itself part of the signed content -- a
    signature captured for one transaction can't be replayed against a
    different transaction_reference to forge success on it.
    """
    broker_headers, payment = await _setup_in_flight_payment(client, db_session)
    transaction_ref = payment["squad_transaction_ref"]

    genuine_signature = compute_dynamic_va_signature(
        secret_key=get_settings().squad_secret_key,
        transaction_reference=transaction_ref,
        amount_received="500000",
        merchant_reference=transaction_ref,
    )

    redirected_ref = f"attacker-controlled-{uuid.uuid4()}"
    webhook_resp = await client.post(
        "/api/v1/webhooks/squad",
        json={
            "transaction_reference": redirected_ref,
            "amount_received": "500000",
            "merchant_reference": redirected_ref,
            "transaction_type": "dynamic_virtual_account",
        },
        headers={"x-squad-encrypted-body": genuine_signature},
    )
    assert webhook_resp.status_code == 200, webhook_resp.text

    event = await db_session.scalar(
        select(WebhookEvent).where(WebhookEvent.transaction_ref == redirected_ref)
    )
    assert event is not None
    assert event.signature_valid is False
    assert event.processing_status == "rejected"

    original_payment = await db_session.scalar(
        select(Payment).where(Payment.squad_transaction_ref == transaction_ref)
    )
    assert original_payment is not None
    assert original_payment.status == "initiated"
    assert fake_squad_client.transfers == []
