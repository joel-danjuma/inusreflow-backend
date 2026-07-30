import uuid
from datetime import date
from typing import Any

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.integrations.squad.signature import compute_static_va_signature
from app.models.payment import Payment
from app.models.webhook_event import WebhookEvent
from tests.fakes import FakeSquadClient
from tests.helpers import (
    assign_broker_to_insurer,
    create_policy,
    create_policyholder,
    onboard_and_approve_broker,
    onboard_and_approve_insurance_company,
    seed_and_activate_insureflow_admin,
)


async def _setup_in_flight_payment(
    client: AsyncClient, db_session: AsyncSession
) -> tuple[dict[str, str], dict[str, Any], dict[str, Any]]:
    """Onboards an approved+assigned insurer/broker pair and creates one
    in-flight Payment (status='initiated'). Returns (broker_headers, payment,
    broker) so callers have the VA number and broker id for building SVA
    webhook signatures.
    """
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, company_headers = await onboard_and_approve_insurance_company(
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

    policyholder = await create_policyholder(
        client,
        company_headers,
        broker_id=broker["id"],
        full_name="Sig Tamper Payer",
        email=f"{uuid.uuid4()}@example.com",
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
        headers={**broker_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert create_resp.status_code == 201, create_resp.text
    return broker_headers, create_resp.json(), broker


async def test_webhook_signature_does_not_cover_a_tampered_principal_amount(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """A genuine SVA signature is computed over principal_amount. An attacker
    who captures a real signature for amount=500000 cannot reuse it against
    a webhook claiming a different (lower) principal_amount -- the
    x-squad-signature will not verify.
    """
    broker_headers, payment, broker = await _setup_in_flight_payment(client, db_session)
    va_number = payment["squad_virtual_account_number"]
    squad_tx_ref = str(uuid.uuid4())
    currency = "NGN"
    broker_id = broker["id"]

    # Genuine signature computed for principal_amount=500000.
    genuine_signature = compute_static_va_signature(
        secret_key=get_settings().squad_secret_key,
        transaction_reference=squad_tx_ref,
        virtual_account_number=va_number,
        currency=currency,
        principal_amount="500000",
        settled_amount="500000",
        customer_identifier=broker_id,
    )

    # Attacker tampers principal_amount to "1" but keeps the original signature.
    webhook_resp = await client.post(
        "/api/v1/webhooks/squad",
        json={
            "transaction_reference": squad_tx_ref,
            "virtual_account_number": va_number,
            "principal_amount": "1",
            "settled_amount": "1",
            "customer_identifier": broker_id,
            "transaction_type": "static_virtual_account",
            "currency": currency,
        },
        headers={"x-squad-signature": genuine_signature},
    )
    assert webhook_resp.status_code == 200, webhook_resp.text

    get_resp = await client.get(f"/api/v1/payments/{payment['id']}", headers=broker_headers)
    assert get_resp.json()["status"] == "initiated"
    assert fake_squad_client.transfers == []

    event = await db_session.scalar(
        select(WebhookEvent).where(WebhookEvent.transaction_ref == squad_tx_ref)
    )
    assert event is not None
    assert event.signature_valid is False
    assert event.processing_status == "rejected"


async def test_webhook_signature_does_not_redirect_to_a_different_transaction_reference(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """transaction_reference is part of the SVA signed payload -- a
    signature captured for squad_tx_ref_A cannot be replayed with
    transaction_reference=squad_tx_ref_B to forge success on a different event.
    """
    broker_headers, payment, broker = await _setup_in_flight_payment(client, db_session)
    va_number = payment["squad_virtual_account_number"]
    # Our internal squad_transaction_ref (for the payment row lookup later).
    our_internal_ref = payment["squad_transaction_ref"]
    squad_tx_ref = str(uuid.uuid4())
    currency = "NGN"
    broker_id = broker["id"]

    # Genuine signature computed for squad_tx_ref.
    genuine_signature = compute_static_va_signature(
        secret_key=get_settings().squad_secret_key,
        transaction_reference=squad_tx_ref,
        virtual_account_number=va_number,
        currency=currency,
        principal_amount="500000",
        settled_amount="500000",
        customer_identifier=broker_id,
    )

    # Attacker replays the signature with a different transaction_reference.
    redirected_ref = f"attacker-controlled-{uuid.uuid4()}"
    webhook_resp = await client.post(
        "/api/v1/webhooks/squad",
        json={
            "transaction_reference": redirected_ref,
            "virtual_account_number": va_number,
            "principal_amount": "500000",
            "settled_amount": "500000",
            "customer_identifier": broker_id,
            "transaction_type": "static_virtual_account",
            "currency": currency,
        },
        headers={"x-squad-signature": genuine_signature},
    )
    assert webhook_resp.status_code == 200, webhook_resp.text

    # A rejected event is persisted under the redirected ref.
    event = await db_session.scalar(
        select(WebhookEvent).where(WebhookEvent.transaction_ref == redirected_ref)
    )
    assert event is not None
    assert event.signature_valid is False
    assert event.processing_status == "rejected"

    # The original payment, keyed by our internal squad_transaction_ref, is unaffected.
    original_payment = await db_session.scalar(
        select(Payment).where(Payment.squad_transaction_ref == our_internal_ref)
    )
    assert original_payment is not None
    assert original_payment.status == "initiated"
    assert fake_squad_client.transfers == []
