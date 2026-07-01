import uuid
from datetime import date

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.integrations.squad.signature import compute_dynamic_va_signature
from app.models.settlement_payout import SettlementPayout
from tests.fakes import FakeSquadClient
from tests.helpers import (
    assign_broker_to_insurer,
    onboard_and_approve_broker,
    onboard_and_approve_insurance_company,
    seed_and_activate_insureflow_admin,
)

_BANK_CODE = "058"
_ACCOUNT_NUMBER = "0123456789"


def _webhook_signature_headers(*, transaction_ref: str, amount_received: str) -> dict[str, str]:
    signature = compute_dynamic_va_signature(
        secret_key=get_settings().squad_secret_key,
        transaction_reference=transaction_ref,
        amount_received=amount_received,
        merchant_reference=transaction_ref,
    )
    return {"x-squad-encrypted-body": signature}


async def _setup_payable_installment(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> tuple[dict, dict[str, str], dict[str, str], str, str]:
    """Onboards an approved+assigned insurer/broker pair, confirms the
    insurer's settlement account, and creates a policy with a due
    installment. Returns (company, company_headers, broker_headers,
    policy_id, installment_id).
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

    user_resp = await client.post(
        "/api/v1/users",
        json={"full_name": "Pay Payer", "email": "pay.payer@example.com"},
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
    installments = installments_resp.json()
    installment_id = installments[0]["id"]

    return company, company_headers, broker_headers, policy["id"], installment_id


async def test_single_payment_success_settles_and_marks_installment_paid(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    company, _, broker_headers, policy_id, installment_id = await _setup_payable_installment(
        client, db_session, fake_squad_client
    )

    create_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": installment_id},
        headers={**broker_headers, "Idempotency-Key": "pay-key-1"},
    )
    assert create_resp.status_code == 201, create_resp.text
    payment = create_resp.json()
    assert payment["status"] == "initiated"
    assert payment["squad_virtual_account_number"]

    # Replaying the same Idempotency-Key must not mint a second VA / Payment.
    replay_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": installment_id},
        headers={**broker_headers, "Idempotency-Key": "pay-key-1"},
    )
    assert replay_resp.status_code == 201, replay_resp.text
    assert replay_resp.json()["id"] == payment["id"]
    assert len(fake_squad_client.created_accounts) == 1

    fake_squad_client.simulate_transaction(
        payment["squad_transaction_ref"], status="SUCCESS", amount_received="500000"
    )
    webhook_resp = await client.post(
        "/api/v1/webhooks/squad",
        json={
            "transaction_reference": payment["squad_transaction_ref"],
            "amount_received": "500000",
            "merchant_reference": payment["squad_transaction_ref"],
            "transaction_type": "dynamic_virtual_account",
        },
        headers=_webhook_signature_headers(
            transaction_ref=payment["squad_transaction_ref"], amount_received="500000"
        ),
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
        "/api/v1/webhooks/squad",
        json={
            "transaction_reference": payment["squad_transaction_ref"],
            "amount_received": "500000",
            "merchant_reference": payment["squad_transaction_ref"],
            "transaction_type": "dynamic_virtual_account",
        },
        headers=_webhook_signature_headers(
            transaction_ref=payment["squad_transaction_ref"], amount_received="500000"
        ),
    )
    assert duplicate_resp.status_code == 200
    assert len(fake_squad_client.transfers) == 1


async def test_single_payment_mismatch_never_settles_or_marks_installment_paid(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    company, _, broker_headers, _policy_id, installment_id = await _setup_payable_installment(
        client, db_session, fake_squad_client
    )

    create_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": installment_id},
        headers={**broker_headers, "Idempotency-Key": "pay-key-2"},
    )
    assert create_resp.status_code == 201, create_resp.text
    payment = create_resp.json()

    fake_squad_client.simulate_transaction(
        payment["squad_transaction_ref"], status="MISMATCH", amount_received="100"
    )
    webhook_resp = await client.post(
        "/api/v1/webhooks/squad",
        json={
            "transaction_reference": payment["squad_transaction_ref"],
            "amount_received": "100",
            "merchant_reference": payment["squad_transaction_ref"],
            "transaction_type": "dynamic_virtual_account",
        },
        headers=_webhook_signature_headers(
            transaction_ref=payment["squad_transaction_ref"], amount_received="100"
        ),
    )
    assert webhook_resp.status_code == 200, webhook_resp.text

    get_resp = await client.get(f"/api/v1/payments/{payment['id']}", headers=broker_headers)
    assert get_resp.json()["status"] == "mismatch"

    payout = await db_session.scalar(
        select(SettlementPayout).where(
            SettlementPayout.insurance_company_id == uuid.UUID(company["id"])
        )
    )
    assert payout is None
    assert fake_squad_client.transfers == []


async def test_webhook_with_invalid_signature_is_rejected_and_never_processed(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    _, _, broker_headers, _policy_id, installment_id = await _setup_payable_installment(
        client, db_session, fake_squad_client
    )

    create_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": installment_id},
        headers={**broker_headers, "Idempotency-Key": "pay-key-3"},
    )
    payment = create_resp.json()

    fake_squad_client.simulate_transaction(
        payment["squad_transaction_ref"], status="SUCCESS", amount_received="500000"
    )
    webhook_resp = await client.post(
        "/api/v1/webhooks/squad",
        json={
            "transaction_reference": payment["squad_transaction_ref"],
            "amount_received": "500000",
            "merchant_reference": payment["squad_transaction_ref"],
            "transaction_type": "dynamic_virtual_account",
        },
        headers={"x-squad-encrypted-body": "not-a-real-signature"},
    )
    assert webhook_resp.status_code == 200

    get_resp = await client.get(f"/api/v1/payments/{payment['id']}", headers=broker_headers)
    assert get_resp.json()["status"] == "initiated"
    assert fake_squad_client.transfers == []
