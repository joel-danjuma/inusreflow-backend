import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform_user import PlatformUser
from tests.fakes import FakeSquadClient
from tests.helpers import (
    assign_broker_to_insurer,
    onboard_and_approve_broker,
    onboard_and_approve_insurance_company,
    seed_and_activate_insureflow_admin,
)


async def _onboard(client: AsyncClient, *, name: str, contact_email: str) -> tuple[dict, str]:
    resp = await client.post(
        "/api/v1/brokers",
        json={
            "name": name,
            "contact_email": contact_email,
            "bvn": "22222222222",
            "phone_number": "+2348012345678",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    return body["broker"], body["otp"]


async def test_otp_returned_on_onboard_and_logs_in_while_pending(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    broker, otp = await _onboard(
        client, name="OTP Brokers", contact_email=f"admin-{uuid.uuid4()}@otp-brokers.example.com"
    )
    assert broker["status"] == "pending"
    assert len(otp) == 6 and otp.isdigit()

    login_resp = await client.post(
        "/api/v1/auth/login", data={"username": broker["contact_email"], "password": otp}
    )
    assert login_resp.status_code == 200, login_resp.text
    body = login_resp.json()
    assert body["must_change_password"] is True
    assert body["org_approved"] is False


async def test_full_access_blocked_until_password_changed_and_approved(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    broker, otp = await _onboard(
        client,
        name="Gated Brokers",
        contact_email=f"admin-{uuid.uuid4()}@gated-brokers.example.com",
    )

    login_resp = await client.post(
        "/api/v1/auth/login", data={"username": broker["contact_email"], "password": otp}
    )
    assert login_resp.status_code == 200, login_resp.text
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    summary_resp = await client.get("/api/v1/brokers/me/dashboard-summary", headers=headers)
    assert summary_resp.status_code == 403, summary_resp.text
    get_resp = await client.get(f"/api/v1/brokers/{broker['id']}", headers=headers)
    assert get_resp.status_code == 200, get_resp.text
    assert get_resp.json()["status"] == "pending"

    change_resp = await client.patch(
        "/api/v1/auth/change-password",
        json={"current_password": otp, "new_password": "new-real-password-123"},
        headers=headers,
    )
    assert change_resp.status_code == 200, change_resp.text
    headers = {"Authorization": f"Bearer {change_resp.json()['access_token']}"}

    summary_resp_2 = await client.get("/api/v1/brokers/me/dashboard-summary", headers=headers)
    assert summary_resp_2.status_code == 403, summary_resp_2.text

    approve_resp = await client.patch(
        f"/api/v1/admin/brokers/{broker['id']}/approve", headers=admin_headers
    )
    assert approve_resp.status_code == 200, approve_resp.text

    # get_tenant_id (which require_full_access sits in front of) additionally
    # requires an active insurer assignment for broker roles -- unrelated to
    # the OTP/approval gating this test is actually about, but still a
    # precondition for this particular endpoint to return 200 rather than 409.
    company, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Gated Brokers Insurer",
        contact_email=f"admin-{uuid.uuid4()}@gated-brokers-insurer.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )

    summary_resp_3 = await client.get("/api/v1/brokers/me/dashboard-summary", headers=headers)
    assert summary_resp_3.status_code == 200, summary_resp_3.text


async def test_expired_otp_rejected_at_login(client: AsyncClient, db_session: AsyncSession) -> None:
    broker, otp = await _onboard(
        client,
        name="Expired OTP Brokers",
        contact_email=f"admin-{uuid.uuid4()}@expired-otp-brokers.example.com",
    )
    user = await db_session.scalar(
        select(PlatformUser).where(PlatformUser.email == broker["contact_email"])
    )
    assert user is not None
    user.otp_expires_at = datetime.now(UTC) - timedelta(hours=1)
    await db_session.flush()

    login_resp = await client.post(
        "/api/v1/auth/login", data={"username": broker["contact_email"], "password": otp}
    )
    assert login_resp.status_code == 401, login_resp.text
    assert "expired" in login_resp.json()["detail"].lower()


async def test_reissue_otp_generates_working_new_code(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    broker, otp = await _onboard(
        client,
        name="Reissue Brokers",
        contact_email=f"admin-{uuid.uuid4()}@reissue-brokers.example.com",
    )

    reissue_resp = await client.patch(
        f"/api/v1/admin/brokers/{broker['id']}/reissue-otp", headers=admin_headers
    )
    assert reissue_resp.status_code == 200, reissue_resp.text
    new_otp = reissue_resp.json()["otp"]
    assert new_otp != otp

    old_login = await client.post(
        "/api/v1/auth/login", data={"username": broker["contact_email"], "password": otp}
    )
    assert old_login.status_code == 401, old_login.text

    new_login = await client.post(
        "/api/v1/auth/login", data={"username": broker["contact_email"], "password": new_otp}
    )
    assert new_login.status_code == 200, new_login.text


async def test_broker_staff_otp_login_has_no_approval_gate(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    """Staff creation has no org-approval step at all -- must_change_password
    is the only thing gating a new staff member, and it clears the moment
    they set a real password.
    """
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Staffed OTP Brokers",
        contact_email=f"admin-{uuid.uuid4()}@staffed-otp-brokers.example.com",
    )
    company, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Staffed OTP Brokers Insurer",
        contact_email=f"admin-{uuid.uuid4()}@staffed-otp-brokers-insurer.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )

    staff_email = f"staff-{uuid.uuid4()}@staffed-otp-brokers.example.com"
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
    assert login_resp.status_code == 200, login_resp.text
    assert login_resp.json()["must_change_password"] is True
    # Org is already approved -- unlike onboarding, org_approved is true from the start.
    assert login_resp.json()["org_approved"] is True
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    blocked_resp = await client.get("/api/v1/brokers/me/dashboard-summary", headers=headers)
    assert blocked_resp.status_code == 403, blocked_resp.text

    change_resp = await client.patch(
        "/api/v1/auth/change-password",
        json={"current_password": staff_otp, "new_password": "staff-new-password-123"},
        headers=headers,
    )
    assert change_resp.status_code == 200, change_resp.text
    headers = {"Authorization": f"Bearer {change_resp.json()['access_token']}"}

    allowed_resp = await client.get("/api/v1/brokers/me/dashboard-summary", headers=headers)
    assert allowed_resp.status_code == 200, allowed_resp.text
