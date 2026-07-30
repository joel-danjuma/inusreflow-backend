import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fakes import FakeSquadClient
from tests.helpers import onboard_and_approve_broker, seed_and_activate_insureflow_admin


async def test_broker_admin_can_self_provision_virtual_account(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """Onboarding no longer collects bvn/phone_number upfront -- approval
    proceeds without provisioning a VA, and the broker admin sets both
    themselves afterward via PATCH /virtual-accounts/me.
    """
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Self Service KYB Brokers",
        contact_email=f"admin-{uuid.uuid4()}@self-service-kyb-brokers.example.com",
        bvn="",
        phone_number="",
    )
    assert broker["status"] == "approved"

    before_resp = await client.get("/api/v1/virtual-accounts/me", headers=broker_headers)
    assert before_resp.status_code == 200, before_resp.text
    assert before_resp.json()["squad_va_number"] is None

    update_resp = await client.patch(
        "/api/v1/virtual-accounts/me",
        json={"bvn": "22222222222", "phone_number": "+2348012345678"},
        headers=broker_headers,
    )
    assert update_resp.status_code == 200, update_resp.text
    updated = update_resp.json()
    assert updated["squad_va_number"] is not None
    assert updated["squad_va_bank"] is not None

    after_resp = await client.get("/api/v1/virtual-accounts/me", headers=broker_headers)
    assert after_resp.status_code == 200, after_resp.text
    assert after_resp.json()["squad_va_number"] == updated["squad_va_number"]


async def test_broker_staff_forbidden_from_updating_kyb(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Staffed KYB Brokers",
        contact_email=f"admin-{uuid.uuid4()}@staffed-kyb-brokers.example.com",
    )

    staff_email = f"staff-{uuid.uuid4()}@staffed-kyb-brokers.example.com"
    staff_resp = await client.post(
        f"/api/v1/brokers/{broker['id']}/staff",
        json={"email": staff_email},
        headers=broker_headers,
    )
    assert staff_resp.status_code == 201, staff_resp.text
    staff_otp = staff_resp.json()["otp"]

    login_resp = await client.post(
        "/api/v1/auth/login", data={"username": staff_email, "password": staff_otp}
    )
    login_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
    change_resp = await client.patch(
        "/api/v1/auth/change-password",
        json={"current_password": staff_otp, "new_password": "staff-new-password-123"},
        headers=login_headers,
    )
    staff_headers = {"Authorization": f"Bearer {change_resp.json()['access_token']}"}

    resp = await client.patch(
        "/api/v1/virtual-accounts/me",
        json={"bvn": "22222222222", "phone_number": "+2348012345678"},
        headers=staff_headers,
    )
    assert resp.status_code == 403, resp.text
