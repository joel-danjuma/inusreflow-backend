import uuid
from datetime import date

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fakes import FakeSquadClient
from tests.helpers import (
    assign_broker_to_insurer,
    onboard_and_approve_broker,
    onboard_and_approve_insurance_company,
    seed_and_activate_insureflow_admin,
)

"""Overlap is exercised as sequential calls against the same in-flight-claim
checks (payment_service / bulk_payment_service), not as true concurrent
requests -- AsyncSession isn't safe for concurrent reentrant use, and
Postgres's own transaction serialization doesn't need re-proving here; only
the application-level rejection logic (ConflictError on a second claim over
the same installment) does.
"""


async def _setup_due_installments(
    client: AsyncClient, db_session: AsyncSession, *, num_installments: int = 3
) -> tuple[dict[str, str], list[str]]:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)

    company, _company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Overlap Insurance",
        contact_email=f"admin-{uuid.uuid4()}@overlap-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Overlap Brokers",
        contact_email=f"admin-{uuid.uuid4()}@overlap-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )

    user_resp = await client.post(
        "/api/v1/users",
        json={"full_name": "Overlap Payer", "email": "overlap.payer@example.com"},
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

    return broker_headers, installment_ids


async def test_bulk_then_bulk_overlapping_installment_is_rejected(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    broker_headers, installment_ids = await _setup_due_installments(client, db_session)
    id0, id1, id2 = installment_ids

    first_resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": [id0, id1]},
        headers={**broker_headers, "Idempotency-Key": "overlap-bulk-a"},
    )
    assert first_resp.status_code == 201, first_resp.text

    second_resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": [id1, id2]},
        headers={**broker_headers, "Idempotency-Key": "overlap-bulk-b"},
    )
    assert second_resp.status_code == 409, second_resp.text
    assert len(fake_squad_client.created_accounts) == 1


async def test_bulk_then_single_overlapping_installment_is_rejected(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    broker_headers, installment_ids = await _setup_due_installments(client, db_session)
    id0, id1, _id2 = installment_ids

    bulk_resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": [id0, id1]},
        headers={**broker_headers, "Idempotency-Key": "overlap-bulk-c"},
    )
    assert bulk_resp.status_code == 201, bulk_resp.text

    single_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": id1},
        headers={**broker_headers, "Idempotency-Key": "overlap-single-a"},
    )
    assert single_resp.status_code == 409, single_resp.text
    assert len(fake_squad_client.created_accounts) == 1


async def test_single_then_bulk_overlapping_installment_is_rejected(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    broker_headers, installment_ids = await _setup_due_installments(client, db_session)
    id0, id1, _id2 = installment_ids

    single_resp = await client.post(
        "/api/v1/payments",
        json={"installment_id": id0},
        headers={**broker_headers, "Idempotency-Key": "overlap-single-b"},
    )
    assert single_resp.status_code == 201, single_resp.text

    bulk_resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": [id0, id1]},
        headers={**broker_headers, "Idempotency-Key": "overlap-bulk-d"},
    )
    assert bulk_resp.status_code == 409, bulk_resp.text
    assert len(fake_squad_client.created_accounts) == 1
