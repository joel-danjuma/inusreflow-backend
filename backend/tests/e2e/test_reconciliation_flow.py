import uuid
from datetime import timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.settlement_payout import SettlementPayout
from app.services import reconciliation_service
from tests.e2e.test_bulk_payment_flow import _build_sva_webhook as _bulk_build_sva_webhook
from tests.e2e.test_bulk_payment_flow import _setup_payable_installments
from tests.e2e.test_single_payment_flow import _build_sva_webhook, _setup_payable_installment
from tests.fakes import FakeSquadClient
from tests.helpers import seed_and_activate_insureflow_admin


async def test_reconciliation_skips_sva_payment_without_webhook_tx_ref(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """For SVA payments, Squad's transaction_reference is only known after
    a webhook arrives. If no webhook has fired (squad_webhook_tx_ref is None),
    reconciliation skips the payment and relies on Squad's 24 h retry policy
    rather than guessing the outcome. The payment is counted as stale but
    not resolved.
    """
    _, _, _broker, broker_headers, _policy_id, installment_id = await _setup_payable_installment(
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

    # No webhook posted -- squad_webhook_tx_ref remains None.
    result = await reconciliation_service.reconcile_transactions(
        db_session,
        squad_client=fake_squad_client,
        merchant_id=get_settings().squad_merchant_id,
        stale_after=timedelta(seconds=-1),
    )
    # Counted as stale but skipped -- cannot requery without squad_webhook_tx_ref.
    assert result.payments_checked == 1
    assert result.payments_resolved == 0

    get_resp = await client.get(f"/api/v1/payments/{payment['id']}", headers=broker_headers)
    assert get_resp.json()["status"] == "initiated"


async def test_reconciliation_resolves_payment_where_initial_requery_failed(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """Simulates the case where Squad fires a webhook (setting squad_webhook_tx_ref
    on the Payment) but the mandatory re-query returns None -- so the webhook
    event is marked FAILED and the payment stays 'initiated'. A subsequent
    reconciliation run retries the requery successfully and resolves the payment
    through the exact same payment_service.resolve_payment_outcome entry point,
    with settlement firing exactly once.
    """
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
        headers={**broker_headers, "Idempotency-Key": "reconcile-key-2"},
    )
    assert create_resp.status_code == 201, create_resp.text
    payment = create_resp.json()
    va_number = payment["squad_virtual_account_number"]

    # Post webhook WITHOUT scripting verify_transaction (returns None) ->
    # sets squad_webhook_tx_ref but marks the webhook event FAILED.
    squad_tx_ref = str(uuid.uuid4())
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

    # Payment still initiated -- requery returned None.
    get_resp = await client.get(f"/api/v1/payments/{payment['id']}", headers=broker_headers)
    assert get_resp.json()["status"] == "initiated"

    # Now script verify_transaction to succeed.
    fake_squad_client.simulate_transaction(squad_tx_ref, status="SUCCESS")

    result = await reconciliation_service.reconcile_transactions(
        db_session,
        squad_client=fake_squad_client,
        merchant_id=get_settings().squad_merchant_id,
        stale_after=timedelta(seconds=-1),
    )
    assert result.payments_checked == 1
    assert result.payments_resolved == 1

    get_resp2 = await client.get(f"/api/v1/payments/{payment['id']}", headers=broker_headers)
    assert get_resp2.json()["status"] == "success"

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

    # A second reconciliation run sees no stale initiated payments.
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
    _, _, _broker, broker_headers, _policy_id, installment_id = await _setup_payable_installment(
        client, db_session, fake_squad_client
    )

    create_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": installment_id},
        headers={**broker_headers, "Idempotency-Key": "reconcile-key-3"},
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


async def test_reconciliation_resolves_a_payment_batch_where_requery_initially_failed(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """Same requery-failure recovery path as for single payments, but for a
    bulk PaymentBatch -- still settles exactly once for the batch total.
    """
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, _, broker, broker_headers, installment_ids = await _setup_payable_installments(
        client, db_session, fake_squad_client, admin_headers, label="Reconcile"
    )

    create_resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": installment_ids},
        headers={**broker_headers, "Idempotency-Key": "reconcile-bulk-key-1"},
    )
    assert create_resp.status_code == 201, create_resp.text
    batch = create_resp.json()
    va_number = batch["squad_virtual_account_number"]
    total_amount_kobo = batch["total_amount_kobo"]

    # Post webhook without scripting verify_transaction (returns None) ->
    # sets squad_webhook_tx_ref on the batch but leaves it initiated.
    squad_tx_ref = str(uuid.uuid4())
    webhook_payload, webhook_headers = _bulk_build_sva_webhook(
        squad_tx_ref=squad_tx_ref,
        va_number=va_number,
        amount_kobo=total_amount_kobo,
        broker_id=broker["id"],
    )
    await client.post("/api/v1/webhooks/squad", json=webhook_payload, headers=webhook_headers)

    # Now script verify_transaction to succeed.
    fake_squad_client.simulate_transaction(squad_tx_ref, status="SUCCESS")

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
    company, _, broker, broker_headers, installment_ids = await _setup_payable_installments(
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
    va_number = payment["squad_virtual_account_number"]

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
