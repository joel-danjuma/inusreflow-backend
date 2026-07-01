import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.commission_service import resolve_commission_config
from tests.helpers import (
    assign_broker_to_insurer,
    onboard_and_approve_broker,
    onboard_and_approve_insurance_company,
    seed_and_activate_insureflow_admin,
)


async def test_commission_config_scope_writes_resolution_and_visibility(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)

    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Commission Test Insurance",
        contact_email="admin@commission-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Commission Test Brokers",
        contact_email="admin@commission-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )

    other_broker, _other_broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Unassigned Brokers",
        contact_email="admin@unassigned-brokers.example.com",
    )

    # Insurance Company Admin cannot write a global-scope rate.
    forbidden_resp = await client.post(
        "/api/v1/commission-configs",
        json={"scope": "global", "gtbank_rate_bps": 60, "insureflow_rate_bps": 60},
        headers=company_headers,
    )
    assert forbidden_resp.status_code == 403

    # Insurance Company Admin cannot set a broker-scope rate for a broker
    # that isn't currently assigned to them.
    not_found_resp = await client.post(
        "/api/v1/commission-configs",
        json={
            "scope": "broker",
            "broker_id": other_broker["id"],
            "gtbank_rate_bps": 50,
            "insureflow_rate_bps": 50,
            "broker_rate_bps": 300,
        },
        headers=company_headers,
    )
    assert not_found_resp.status_code == 404

    # Insurance Company Admin sets a broker-scope rate for their own broker.
    broker_scope_resp = await client.post(
        "/api/v1/commission-configs",
        json={
            "scope": "broker",
            "broker_id": broker["id"],
            "gtbank_rate_bps": 50,
            "insureflow_rate_bps": 50,
            "broker_rate_bps": 300,
        },
        headers=company_headers,
    )
    assert broker_scope_resp.status_code == 201, broker_scope_resp.text
    assert broker_scope_resp.json()["broker_rate_bps"] == 300

    # Insureflow Admin updates the global rate -- closes the seeded row,
    # inserts a fresh one, never updates in place (PRD §9).
    global_resp = await client.post(
        "/api/v1/commission-configs",
        json={"scope": "global", "gtbank_rate_bps": 75, "insureflow_rate_bps": 75},
        headers=admin_headers,
    )
    assert global_resp.status_code == 201, global_resp.text

    # Resolution: the broker has its own override, so it wins over global.
    resolved_for_broker = await resolve_commission_config(
        db_session,
        broker_id=uuid.UUID(broker["id"]),
        insurance_company_id=uuid.UUID(company["id"]),
    )
    assert resolved_for_broker.scope == "broker"
    assert resolved_for_broker.broker_rate_bps == 300

    # The unassigned broker has no override, so it falls through to the
    # newly-updated global rate.
    resolved_for_other_broker = await resolve_commission_config(
        db_session,
        broker_id=uuid.UUID(other_broker["id"]),
        insurance_company_id=uuid.UUID(company["id"]),
    )
    assert resolved_for_other_broker.scope == "global"
    assert resolved_for_other_broker.gtbank_rate_bps == 75

    # Both the insurer's admin and the broker's own admin can see the global
    # rate plus the broker's own commission row.
    company_list_resp = await client.get("/api/v1/commission-configs", headers=company_headers)
    assert company_list_resp.status_code == 200
    company_scopes = {row["scope"] for row in company_list_resp.json()}
    assert company_scopes == {"global", "broker"}

    broker_list_resp = await client.get("/api/v1/commission-configs", headers=broker_headers)
    assert broker_list_resp.status_code == 200
    broker_scopes = {row["scope"] for row in broker_list_resp.json()}
    assert broker_scopes == {"global", "broker"}
