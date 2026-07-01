import uuid
from datetime import timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.integrations.squad.signature import compute_dynamic_va_signature
from app.models.settlement_payout import SettlementPayout
from app.services import reconciliation_service
from tests.e2e.test_bulk_payment_flow import _setup_payable_installments
from tests.e2e.test_single_payment_flow import _setup_payable_installment
from tests.fakes import FakeSquadClient
from tests.helpers import seed_and_activate_insureflow_admin

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


async def test_reconciliation_resolves_a_payment_whose_webhook_was_never_delivered(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """Simulates a missed webhook -- Squad's own callback never arrives -- and
    confirms the periodic reconciliation job still resolves the payment to
    the same final state a normal webhook delivery would have, through the
    exact same entry point (payment_service.resolve_payment_outcome), with
    settlement firing exactly once.
    """
    company, _, broker_headers, policy_id, installment_id = await _setup_payable_installment(
        client, db_session, fake_squad_client
    )

    create_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": installment_id},
        headers={**broker_headers, "Idempotency-Key": "reconcile-key-1"},
    )
    assert create_resp.status_code == 201, create_resp.text
    payment = create_resp.json()
    assert payment["status"] == "initiated"

    fake_squad_client.simulate_transaction(
        payment["squad_transaction_ref"], status="SUCCESS", amount_received="500000"
    )
    # No POST /webhooks/squad call here -- the webhook is "lost".

    result = await reconciliation_service.reconcile_transactions(
        db_session,
        squad_client=fake_squad_client,
        merchant_id=get_settings().squad_merchant_id,
        stale_after=timedelta(seconds=-1),
    )
    assert result.payments_checked == 1
    assert result.payments_resolved == 1

    get_resp = await client.get(f"/api/v1/payments/{payment['id']}", headers=broker_headers)
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

    # A real webhook arriving afterwards (Squad's own retry) is still a no-op.
    rerun_result = await reconciliation_service.reconcile_transactions(
        db_session,
        squad_client=fake_squad_client,
        merchant_id=get_settings().squad_merchant_id,
        stale_after=timedelta(seconds=-1),
    )
    assert rerun_result.payments_checked == 0
    assert len(fake_squad_client.transfers) == 1


async def test_reconciliation_leaves_a_fresh_initiated_payment_alone(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """A Payment that's merely 'initiated' but still within the staleness
    window (the common case -- the customer just hasn't paid yet) must not be
    touched by reconciliation.
    """
    _, _, broker_headers, _policy_id, installment_id = await _setup_payable_installment(
        client, db_session, fake_squad_client
    )

    create_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": installment_id},
        headers={**broker_headers, "Idempotency-Key": "reconcile-key-2"},
    )
    assert create_resp.status_code == 201, create_resp.text
    payment = create_resp.json()

    result = await reconciliation_service.reconcile_transactions(
        db_session,
        squad_client=fake_squad_client,
        merchant_id=get_settings().squad_merchant_id,
        stale_after=timedelta(minutes=30),
    )
    assert result.payments_checked == 0
    assert result.payments_resolved == 0

    get_resp = await client.get(f"/api/v1/payments/{payment['id']}", headers=broker_headers)
    assert get_resp.json()["status"] == "initiated"


async def test_reconciliation_resolves_a_payment_batch_whose_webhook_was_never_delivered(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """Same missed-webhook recovery, but for a bulk PaymentBatch -- still
    settles exactly once for the batch total, never one payout per item.
    """
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, _, broker_headers, installment_ids = await _setup_payable_installments(
        client, db_session, fake_squad_client, admin_headers, label="Reconcile"
    )

    create_resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": installment_ids},
        headers={**broker_headers, "Idempotency-Key": "reconcile-bulk-key-1"},
    )
    assert create_resp.status_code == 201, create_resp.text
    batch = create_resp.json()

    total_amount_kobo = batch["total_amount_kobo"]
    fake_squad_client.simulate_transaction(
        batch["squad_transaction_ref"], status="SUCCESS", amount_received=str(total_amount_kobo)
    )
    # No POST /webhooks/squad call here -- the webhook is "lost".

    result = await reconciliation_service.reconcile_transactions(
        db_session,
        squad_client=fake_squad_client,
        merchant_id=get_settings().squad_merchant_id,
        stale_after=timedelta(seconds=-1),
    )
    assert result.batches_checked == 1
    assert result.batches_resolved == 1

    get_resp = await client.get(f"/api/v1/payments/bulk/{batch['id']}", headers=broker_headers)
    assert get_resp.json()["status"] == "success"

    installments_resp = await client.get(
        "/api/v1/installments", headers=broker_headers, params={"status": "paid"}
    )
    paid_ids = {i["id"] for i in installments_resp.json()}
    for installment_id in installment_ids:
        assert installment_id in paid_ids

    payout = await db_session.scalar(
        select(SettlementPayout).where(
            SettlementPayout.insurance_company_id == uuid.UUID(company["id"])
        )
    )
    assert payout is not None
    assert payout.status == "success"
    assert len(fake_squad_client.transfers) == 1


async def test_retry_settlement_payout_endpoint_mints_fresh_attempt_and_is_admin_only(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """The settlement payout for a successful payment fails because the
    initial Squad transfer call itself errors; once the transient issue is
    gone, only an Insureflow Admin can trigger a retry (RBAC), and the retry
    mints a fresh squad_transfer_ref rather than reusing the failed one
    (CLAUDE.md's never-reuse-a-failed-reference invariant).
    """
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, _, broker_headers, installment_ids = await _setup_payable_installments(
        client, db_session, fake_squad_client, admin_headers, label="RetryFlow", num_installments=1
    )
    installment_id = installment_ids[0]

    fake_squad_client.fail_transfer = True
    create_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": installment_id},
        headers={**broker_headers, "Idempotency-Key": "retry-key-1"},
    )
    assert create_resp.status_code == 201, create_resp.text
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
        headers=_webhook_signature_headers(
            transaction_ref=payment["squad_transaction_ref"], amount_received="500000"
        ),
    )
    assert webhook_resp.status_code == 200, webhook_resp.text

    failed_payout = await db_session.scalar(
        select(SettlementPayout).where(
            SettlementPayout.insurance_company_id == uuid.UUID(company["id"])
        )
    )
    assert failed_payout is not None
    assert failed_payout.status == "failed"
    assert fake_squad_client.transfers == []

    fake_squad_client.fail_transfer = False

    forbidden_resp = await client.post(
        f"/api/v1/settlements/{failed_payout.id}/retry", headers=broker_headers
    )
    assert forbidden_resp.status_code == 403

    retry_resp = await client.post(
        f"/api/v1/settlements/{failed_payout.id}/retry", headers=admin_headers
    )
    assert retry_resp.status_code == 200, retry_resp.text
    retried = retry_resp.json()
    assert retried["status"] == "success"
    assert retried["attempt_number"] == 2
    assert retried["previous_attempt_id"] == str(failed_payout.id)
    assert retried["squad_transfer_ref"] != failed_payout.squad_transfer_ref
    assert len(fake_squad_client.transfers) == 1

    second_retry_resp = await client.post(
        f"/api/v1/settlements/{failed_payout.id}/retry", headers=admin_headers
    )
    assert second_retry_resp.status_code == 409
