import uuid

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

import app.core.rate_limit as rate_limit
from app.core.config import get_settings
from tests.fakes import FakeSquadClient
from tests.helpers import (
    assign_broker_to_insurer,
    onboard_and_approve_broker,
    onboard_and_approve_insurance_company,
    seed_and_activate_insureflow_admin,
)


async def test_payment_rate_limit_blocks_a_broker_past_its_per_minute_cap(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    fake_squad_client: FakeSquadClient,
) -> None:
    """Settings.payment_rate_limit_per_broker_per_minute (PRD §11.5,
    CLAUDE.md) is enforced as a FastAPI dependency on the route, so it runs
    before the handler ever looks up the installment -- the 3rd request
    here must come back 429 even though the installment_id is nonsense and
    would otherwise 404.
    """
    low_limit_settings = get_settings().model_copy(
        update={"payment_rate_limit_per_broker_per_minute": 2}
    )
    monkeypatch.setattr(rate_limit, "get_settings", lambda: low_limit_settings)

    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Rate Limit Insurance",
        contact_email=f"admin-{uuid.uuid4()}@rate-limit-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Rate Limit Brokers",
        contact_email=f"admin-{uuid.uuid4()}@rate-limit-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )

    payload = {"installment_id": str(uuid.uuid4())}

    def _post() -> object:
        return client.post(
            "/api/v1/payments",
            json=payload,
            headers={**broker_headers, "Idempotency-Key": str(uuid.uuid4())},
        )

    first = await _post()
    second = await _post()
    third = await _post()

    assert first.status_code == status.HTTP_404_NOT_FOUND, first.text
    assert second.status_code == status.HTTP_404_NOT_FOUND, second.text
    assert third.status_code == status.HTTP_429_TOO_MANY_REQUESTS, third.text


async def test_payment_rate_limit_is_scoped_per_broker(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    fake_squad_client: FakeSquadClient,
) -> None:
    """A second broker exhausting its own limit must never affect the first
    -- the counter key includes broker_id, not just the endpoint/window.
    """
    low_limit_settings = get_settings().model_copy(
        update={"payment_rate_limit_per_broker_per_minute": 1}
    )
    monkeypatch.setattr(rate_limit, "get_settings", lambda: low_limit_settings)

    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Rate Limit Insurance Two",
        contact_email=f"admin-{uuid.uuid4()}@rate-limit-insurance-two.example.com",
    )
    broker_a, broker_a_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Rate Limit Brokers A",
        contact_email=f"admin-{uuid.uuid4()}@rate-limit-brokers-a.example.com",
    )
    broker_b, broker_b_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Rate Limit Brokers B",
        contact_email=f"admin-{uuid.uuid4()}@rate-limit-brokers-b.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker_a["id"], insurance_company_id=company["id"]
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker_b["id"], insurance_company_id=company["id"]
    )

    payload = {"installment_id": str(uuid.uuid4())}

    a_first = await client.post(
        "/api/v1/payments",
        json=payload,
        headers={**broker_a_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    a_second = await client.post(
        "/api/v1/payments",
        json=payload,
        headers={**broker_a_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    b_first = await client.post(
        "/api/v1/payments",
        json=payload,
        headers={**broker_b_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert a_first.status_code == status.HTTP_404_NOT_FOUND, a_first.text
    assert a_second.status_code == status.HTTP_429_TOO_MANY_REQUESTS, a_second.text
    assert b_first.status_code == status.HTTP_404_NOT_FOUND, b_first.text
