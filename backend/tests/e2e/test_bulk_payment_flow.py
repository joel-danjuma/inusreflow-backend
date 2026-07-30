import uuid
from datetime import date
from typing import Any

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.integrations.squad.signature import compute_static_va_signature
from app.models.ledger_entry import LedgerEntry
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
    """Returns (payload, headers) for a correctly-signed SVA webhook."""
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


async def _setup_payable_installments(
    client: AsyncClient,
    db_session: AsyncSession,
    fake_squad_client: FakeSquadClient,
    admin_headers: dict[str, str],
    *,
    label: str,
    num_installments: int = 2,
) -> tuple[dict, dict[str, str], dict, dict[str, str], list[str]]:
    """Mirrors test_single_payment_flow._setup_payable_installment but returns
    several due installment ids for bulk collection. Returns
    (company, company_headers, broker, broker_headers, installment_ids).

    broker is returned so callers have the broker id for building SVA webhook
    customer_identifier (= str(broker.id) by VA creation convention).
    """
    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name=f"{label} Insurance",
        contact_email=f"admin-{uuid.uuid4()}@{label.lower()}-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name=f"{label} Brokers",
        contact_email=f"admin-{uuid.uuid4()}@{label.lower()}-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )

    fake_squad_client.set_payout_account(
        bank_code=_BANK_CODE,
        account_number=_ACCOUNT_NUMBER,
        account_name=f"{label} Insurance Settlement",
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
        full_name=f"{label} Payer",
        email=f"{label.lower()}.payer@example.com",
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
    installment_ids = [i["id"] for i in installments_resp.json()[:num_installments]]
    assert len(installment_ids) == num_installments

    return company, company_headers, broker, broker_headers, installment_ids


async def test_bulk_payment_success_settles_once_for_whole_batch(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, _, broker, broker_headers, installment_ids = await _setup_payable_installments(
        client, db_session, fake_squad_client, admin_headers, label="Bulk"
    )

    create_resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": installment_ids},
        headers={**broker_headers, "Idempotency-Key": "bulk-key-1"},
    )
    assert create_resp.status_code == 201, create_resp.text
    batch = create_resp.json()
    assert batch["status"] == "initiated"
    assert batch["item_count"] == len(installment_ids)
    assert batch["total_amount_kobo"] == 500_000 * len(installment_ids)
    va_number = batch["squad_virtual_account_number"]
    assert va_number
    assert len(batch["items"]) == len(installment_ids)

    # Replaying the same Idempotency-Key must not create another batch.
    replay_resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": installment_ids},
        headers={**broker_headers, "Idempotency-Key": "bulk-key-1"},
    )
    assert replay_resp.status_code == 201, replay_resp.text
    assert replay_resp.json()["id"] == batch["id"]
    # Only 1 VA should exist -- created at broker approval, not during payment.
    assert len(fake_squad_client.created_accounts) == 1

    total_amount_kobo = batch["total_amount_kobo"]
    squad_tx_ref = str(uuid.uuid4())
    fake_squad_client.simulate_transaction(squad_tx_ref, status="SUCCESS")
    webhook_payload, webhook_headers = _build_sva_webhook(
        squad_tx_ref=squad_tx_ref,
        va_number=va_number,
        amount_kobo=total_amount_kobo,
        broker_id=broker["id"],
    )
    webhook_resp = await client.post(
        "/api/v1/webhooks/squad", json=webhook_payload, headers=webhook_headers
    )
    assert webhook_resp.status_code == 200, webhook_resp.text

    get_resp = await client.get(f"/api/v1/payments/bulk/{batch['id']}", headers=broker_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "success"

    installments_resp = await client.get(
        "/api/v1/installments", headers=broker_headers, params={"status": "paid"}
    )
    paid_ids = {i["id"] for i in installments_resp.json()}
    for installment_id in installment_ids:
        assert installment_id in paid_ids

    # Exactly one settlement transfer for the whole batch, never one per item.
    payout = await db_session.scalar(
        select(SettlementPayout).where(
            SettlementPayout.insurance_company_id == uuid.UUID(company["id"])
        )
    )
    assert payout is not None
    assert payout.status == "success"
    assert len(fake_squad_client.transfers) == 1

    # One ledger posting_group_id per item, not per batch.
    entries = (
        await db_session.scalars(
            select(LedgerEntry).where(LedgerEntry.reference_type == "payment_batch_item")
        )
    ).all()
    posting_groups = {entry.posting_group_id for entry in entries}
    assert len(posting_groups) == len(installment_ids)

    # A duplicate webhook delivery (Squad's own retry) must be a no-op.
    duplicate_resp = await client.post(
        "/api/v1/webhooks/squad", json=webhook_payload, headers=webhook_headers
    )
    assert duplicate_resp.status_code == 200
    assert len(fake_squad_client.transfers) == 1


async def test_bulk_payment_failure_never_settles_or_marks_installments_paid(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """A non-SUCCESS Squad verify_transaction result ends the batch as
    'failed' (SVA has no MISMATCH/EXPIRED concepts) without any settlement
    transfer or installment state change.
    """
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, _, broker, broker_headers, installment_ids = await _setup_payable_installments(
        client, db_session, fake_squad_client, admin_headers, label="BulkFailed"
    )

    create_resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": installment_ids},
        headers={**broker_headers, "Idempotency-Key": "bulk-key-2"},
    )
    assert create_resp.status_code == 201, create_resp.text
    batch = create_resp.json()
    va_number = batch["squad_virtual_account_number"]
    total_amount_kobo = batch["total_amount_kobo"]

    squad_tx_ref = str(uuid.uuid4())
    fake_squad_client.simulate_transaction(squad_tx_ref, status="FAILED")
    webhook_payload, webhook_headers = _build_sva_webhook(
        squad_tx_ref=squad_tx_ref,
        va_number=va_number,
        amount_kobo=total_amount_kobo,
        broker_id=broker["id"],
    )
    webhook_resp = await client.post(
        "/api/v1/webhooks/squad", json=webhook_payload, headers=webhook_headers
    )
    assert webhook_resp.status_code == 200, webhook_resp.text

    get_resp = await client.get(f"/api/v1/payments/bulk/{batch['id']}", headers=broker_headers)
    assert get_resp.json()["status"] == "failed"

    payout = await db_session.scalar(
        select(SettlementPayout).where(
            SettlementPayout.insurance_company_id == uuid.UUID(company["id"])
        )
    )
    assert payout is None
    assert fake_squad_client.transfers == []

    installments_resp = await client.get(
        "/api/v1/installments", headers=broker_headers, params={"status": "due"}
    )
    due_ids = {i["id"] for i in installments_resp.json()}
    for installment_id in installment_ids:
        assert installment_id in due_ids


async def test_bulk_payment_rejects_installment_owned_by_another_broker(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    _, _, _broker_a, broker_a_headers, broker_a_installment_ids = await _setup_payable_installments(
        client, db_session, fake_squad_client, admin_headers, label="BulkOwnerA"
    )
    (
        _,
        _,
        _broker_b,
        _broker_b_headers,
        broker_b_installment_ids,
    ) = await _setup_payable_installments(
        client, db_session, fake_squad_client, admin_headers, label="BulkOwnerB"
    )

    # Two VAs were created (one per broker), count them before the rejected request.
    va_count_before = len(fake_squad_client.created_accounts)
    mixed_ids = [broker_a_installment_ids[0], broker_b_installment_ids[0]]
    resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": mixed_ids},
        headers={**broker_a_headers, "Idempotency-Key": "bulk-key-cross-tenant"},
    )
    assert resp.status_code == 404, resp.text
    # Failed validation must not trigger any new Squad VA creation.
    assert len(fake_squad_client.created_accounts) == va_count_before


async def test_bulk_payment_rejects_batch_exceeding_cap(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    settings = get_settings()
    _, _, _broker, broker_headers, installment_ids = await _setup_payable_installments(
        client, db_session, fake_squad_client, admin_headers, label="BulkCap"
    )
    too_many_ids = installment_ids + [
        str(uuid.uuid4()) for _ in range(settings.max_bulk_payment_items)
    ]

    va_count_before = len(fake_squad_client.created_accounts)
    resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": too_many_ids},
        headers={**broker_headers, "Idempotency-Key": "bulk-key-cap"},
    )
    assert resp.status_code == 422, resp.text
    assert len(fake_squad_client.created_accounts) == va_count_before


async def test_ledger_entries_are_scoped_and_broker_forbidden(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    (
        company,
        company_headers,
        broker,
        broker_headers,
        installment_ids,
    ) = await _setup_payable_installments(
        client, db_session, fake_squad_client, admin_headers, label="LedgerList"
    )

    create_resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": installment_ids},
        headers={**broker_headers, "Idempotency-Key": "ledger-list-key"},
    )
    assert create_resp.status_code == 201, create_resp.text
    batch = create_resp.json()

    squad_tx_ref = str(uuid.uuid4())
    fake_squad_client.simulate_transaction(squad_tx_ref, status="SUCCESS")
    webhook_payload, webhook_headers = _build_sva_webhook(
        squad_tx_ref=squad_tx_ref,
        va_number=batch["squad_virtual_account_number"],
        amount_kobo=batch["total_amount_kobo"],
        broker_id=broker["id"],
    )
    webhook_resp = await client.post(
        "/api/v1/webhooks/squad", json=webhook_payload, headers=webhook_headers
    )
    assert webhook_resp.status_code == 200, webhook_resp.text

    insurer_list = await client.get("/api/v1/ledger-entries", headers=company_headers)
    assert insurer_list.status_code == 200, insurer_list.text
    assert len(insurer_list.json()) > 0

    admin_list = await client.get(
        "/api/v1/ledger-entries", headers=admin_headers, params={"broker_id": broker["id"]}
    )
    assert admin_list.status_code == 200, admin_list.text
    assert len(admin_list.json()) > 0
    assert all(e["reference_type"] == "payment_batch_item" for e in admin_list.json())
    assert all(e["account_broker_id"] == broker["id"] for e in admin_list.json())
    assert all(
        e["account_type"] in ("BROKER_CLEARING", "BROKER_COMMISSION") for e in admin_list.json()
    )

    first_batch_item_id = batch["items"][0]["id"]
    reference_filtered = await client.get(
        "/api/v1/ledger-entries",
        headers=admin_headers,
        params={"reference_type": "payment_batch_item", "reference_id": first_batch_item_id},
    )
    assert reference_filtered.status_code == 200, reference_filtered.text
    assert len(reference_filtered.json()) > 0
    assert all(e["reference_id"] == first_batch_item_id for e in reference_filtered.json())

    broker_forbidden = await client.get("/api/v1/ledger-entries", headers=broker_headers)
    assert broker_forbidden.status_code == 403, broker_forbidden.text


async def test_list_bulk_payments_is_scoped_by_role(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    (
        company,
        company_headers,
        broker_a,
        broker_a_headers,
        installment_ids_a,
    ) = await _setup_payable_installments(
        client, db_session, fake_squad_client, admin_headers, label="BulkListA"
    )

    broker_b, broker_b_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="BulkListB Brokers",
        contact_email=f"admin-{uuid.uuid4()}@bulklistb-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker_b["id"], insurance_company_id=company["id"]
    )

    policyholder_b = await create_policyholder(
        client,
        company_headers,
        broker_id=broker_b["id"],
        full_name="BulkListB Payer",
        email="bulklistb.payer@example.com",
    )
    policy_b = await create_policy(
        client,
        company_headers,
        broker_id=broker_b["id"],
        policyholder_id=policyholder_b["id"],
        reference_number=f"DN-{uuid.uuid4()}",
        premium_amount_kobo=500_000,
        start_date=date.today().isoformat(),
    )
    installments_resp = await client.get(
        f"/api/v1/policies/{policy_b['id']}/installments", headers=broker_b_headers
    )
    installment_ids_b = [i["id"] for i in installments_resp.json()[:2]]

    batch_a_resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": installment_ids_a},
        headers={**broker_a_headers, "Idempotency-Key": "bulk-list-key-a"},
    )
    assert batch_a_resp.status_code == 201, batch_a_resp.text
    batch_b_resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": installment_ids_b},
        headers={**broker_b_headers, "Idempotency-Key": "bulk-list-key-b"},
    )
    assert batch_b_resp.status_code == 201, batch_b_resp.text
    batch_a_id = batch_a_resp.json()["id"]
    batch_b_id = batch_b_resp.json()["id"]

    broker_a_list = await client.get("/api/v1/payments/bulk", headers=broker_a_headers)
    assert broker_a_list.status_code == 200, broker_a_list.text
    assert {b["id"] for b in broker_a_list.json()} == {batch_a_id}

    insurer_list = await client.get("/api/v1/payments/bulk", headers=company_headers)
    assert insurer_list.status_code == 200, insurer_list.text
    assert {b["id"] for b in insurer_list.json()} == {batch_a_id, batch_b_id}
    # Each row is a fully-shaped PaymentBatchOut, including its items.
    assert all(row["items"] for row in insurer_list.json())
