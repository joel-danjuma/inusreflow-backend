import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fakes import FakeSquadClient
from tests.helpers import (
    onboard_and_approve_broker,
    onboard_and_approve_insurance_company,
    seed_and_activate_insureflow_admin,
)


async def test_audit_log_lists_state_changes_and_supports_filters(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)

    company, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Audit Log Insurance",
        contact_email=f"admin-{uuid.uuid4()}@audit-log-insurance.example.com",
    )
    await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Audit Log Brokers",
        contact_email=f"admin-{uuid.uuid4()}@audit-log-brokers.example.com",
    )

    all_logs_resp = await client.get("/api/v1/admin/audit-logs", headers=admin_headers)
    assert all_logs_resp.status_code == 200, all_logs_resp.text
    all_logs = all_logs_resp.json()
    actions = {row["action"] for row in all_logs}
    assert "insurance_company.approved" in actions
    assert "broker.approved" in actions

    filtered_resp = await client.get(
        "/api/v1/admin/audit-logs",
        headers=admin_headers,
        params={"action": "insurance_company.approved"},
    )
    assert filtered_resp.status_code == 200, filtered_resp.text
    filtered = filtered_resp.json()
    assert filtered
    assert all(row["action"] == "insurance_company.approved" for row in filtered)
    # This endpoint is intentionally cross-tenant/unscoped (it's an admin
    # audit log, not a tenant-scoped list) -- other insurers' approval
    # events may legitimately appear here too, so only assert this
    # company's own event is present, not that it's the only one.
    assert any(row["entity_id"] == company["id"] for row in filtered)

    entity_filtered_resp = await client.get(
        "/api/v1/admin/audit-logs",
        headers=admin_headers,
        params={"entity_type": "insurance_company"},
    )
    assert entity_filtered_resp.status_code == 200
    assert all(row["entity_type"] == "insurance_company" for row in entity_filtered_resp.json())

    limited_resp = await client.get(
        "/api/v1/admin/audit-logs", headers=admin_headers, params={"limit": 1}
    )
    assert limited_resp.status_code == 200
    assert len(limited_resp.json()) == 1


async def test_audit_log_is_insureflow_admin_only(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    _, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Audit Log Forbidden Insurance",
        contact_email=f"admin-{uuid.uuid4()}@audit-log-forbidden.example.com",
    )
    _, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Audit Log Forbidden Brokers",
        contact_email=f"admin-{uuid.uuid4()}@audit-log-forbidden-brokers.example.com",
    )

    for headers in (company_headers, broker_headers):
        resp = await client.get("/api/v1/admin/audit-logs", headers=headers)
        assert resp.status_code == 403, resp.text
