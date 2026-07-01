import uuid
from datetime import date

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.integrations.squad.signature import compute_dynamic_va_signature
from app.models.ledger_entry import LedgerEntry
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


async def _setup_payable_installments(
    client: AsyncClient,
    db_session: AsyncSession,
    fake_squad_client: FakeSquadClient,
    admin_headers: dict[str, str],
    *,
    label: str,
    num_installments: int = 2,
) -> tuple[dict, dict[str, str], dict[str, str], list[str]]:
    """Mirrors test_single_payment_flow._setup_payable_installment but returns
    several due installment ids from one policy (INSTALLMENT_WINDOW_SIZE=12
    guarantees enough are due) for bulk collection. Takes admin_headers in
    rather than seeding its own, so one test can set up two independent
    tenants without colliding on the bootstrap admin's unique email.
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

    user_resp = await client.post(
        "/api/v1/users",
        json={"full_name": f"{label} Payer", "email": f"{label.lower()}.payer@example.com"},
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
    installment_ids = [i["id"] for i in installments_resp.json()[:num_installments]]
    assert len(installment_ids) == num_installments

    return company, company_headers, broker_headers, installment_ids


async def test_bulk_payment_success_settles_once_for_whole_batch(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, _, broker_headers, installment_ids = await _setup_payable_installments(
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
    assert batch["squad_virtual_account_number"]
    assert len(batch["items"]) == len(installment_ids)

    # Replaying the same Idempotency-Key must not mint a second VA / batch.
    replay_resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": installment_ids},
        headers={**broker_headers, "Idempotency-Key": "bulk-key-1"},
    )
    assert replay_resp.status_code == 201, replay_resp.text
    assert replay_resp.json()["id"] == batch["id"]
    assert len(fake_squad_client.created_accounts) == 1

    total_amount_kobo = batch["total_amount_kobo"]
    fake_squad_client.simulate_transaction(
        batch["squad_transaction_ref"], status="SUCCESS", amount_received=str(total_amount_kobo)
    )
    webhook_resp = await client.post(
        "/api/v1/webhooks/squad",
        json={
            "transaction_reference": batch["squad_transaction_ref"],
            "amount_received": str(total_amount_kobo),
            "merchant_reference": batch["squad_transaction_ref"],
            "transaction_type": "dynamic_virtual_account",
        },
        headers=_webhook_signature_headers(
            transaction_ref=batch["squad_transaction_ref"],
            amount_received=str(total_amount_kobo),
        ),
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
        "/api/v1/webhooks/squad",
        json={
            "transaction_reference": batch["squad_transaction_ref"],
            "amount_received": str(total_amount_kobo),
            "merchant_reference": batch["squad_transaction_ref"],
            "transaction_type": "dynamic_virtual_account",
        },
        headers=_webhook_signature_headers(
            transaction_ref=batch["squad_transaction_ref"],
            amount_received=str(total_amount_kobo),
        ),
    )
    assert duplicate_resp.status_code == 200
    assert len(fake_squad_client.transfers) == 1


async def test_bulk_payment_mismatch_never_settles_or_marks_installments_paid(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, _, broker_headers, installment_ids = await _setup_payable_installments(
        client, db_session, fake_squad_client, admin_headers, label="BulkMismatch"
    )

    create_resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": installment_ids},
        headers={**broker_headers, "Idempotency-Key": "bulk-key-2"},
    )
    assert create_resp.status_code == 201, create_resp.text
    batch = create_resp.json()

    fake_squad_client.simulate_transaction(
        batch["squad_transaction_ref"], status="MISMATCH", amount_received="100"
    )
    webhook_resp = await client.post(
        "/api/v1/webhooks/squad",
        json={
            "transaction_reference": batch["squad_transaction_ref"],
            "amount_received": "100",
            "merchant_reference": batch["squad_transaction_ref"],
            "transaction_type": "dynamic_virtual_account",
        },
        headers=_webhook_signature_headers(
            transaction_ref=batch["squad_transaction_ref"], amount_received="100"
        ),
    )
    assert webhook_resp.status_code == 200, webhook_resp.text

    get_resp = await client.get(f"/api/v1/payments/bulk/{batch['id']}", headers=broker_headers)
    assert get_resp.json()["status"] == "mismatch"

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
    _, _, broker_a_headers, broker_a_installment_ids = await _setup_payable_installments(
        client, db_session, fake_squad_client, admin_headers, label="BulkOwnerA"
    )
    _, _, _broker_b_headers, broker_b_installment_ids = await _setup_payable_installments(
        client, db_session, fake_squad_client, admin_headers, label="BulkOwnerB"
    )

    mixed_ids = [broker_a_installment_ids[0], broker_b_installment_ids[0]]
    resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": mixed_ids},
        headers={**broker_a_headers, "Idempotency-Key": "bulk-key-cross-tenant"},
    )
    assert resp.status_code == 404, resp.text
    assert fake_squad_client.created_accounts == {}


async def test_bulk_payment_rejects_batch_exceeding_cap(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    settings = get_settings()
    _, _, broker_headers, installment_ids = await _setup_payable_installments(
        client, db_session, fake_squad_client, admin_headers, label="BulkCap"
    )
    too_many_ids = installment_ids + [
        str(uuid.uuid4()) for _ in range(settings.max_bulk_payment_items)
    ]

    resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": too_many_ids},
        headers={**broker_headers, "Idempotency-Key": "bulk-key-cap"},
    )
    assert resp.status_code == 422, resp.text
    assert fake_squad_client.created_accounts == {}
