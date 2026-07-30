import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform_user import PlatformUser
from tests.helpers import seed_and_activate_insureflow_admin


async def _onboard(client: AsyncClient, *, name: str, contact_email: str) -> tuple[dict, str]:
    resp = await client.post(
        "/api/v1/insurance-companies", json={"name": name, "contact_email": contact_email}
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    return body["company"], body["otp"]


async def test_otp_returned_on_onboard_and_logs_in_while_pending(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    company, otp = await _onboard(
        client,
        name="OTP Insurance",
        contact_email=f"admin-{uuid.uuid4()}@otp-insurance.example.com",
    )
    assert company["status"] == "pending"
    assert len(otp) == 6 and otp.isdigit()

    login_resp = await client.post(
        "/api/v1/auth/login", data={"username": company["contact_email"], "password": otp}
    )
    assert login_resp.status_code == 200, login_resp.text
    body = login_resp.json()
    assert body["must_change_password"] is True
    assert body["org_approved"] is False


async def test_full_access_blocked_until_password_changed_and_approved(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, otp = await _onboard(
        client,
        name="Gated Insurance",
        contact_email=f"admin-{uuid.uuid4()}@gated-insurance.example.com",
    )

    login_resp = await client.post(
        "/api/v1/auth/login", data={"username": company["contact_email"], "password": otp}
    )
    assert login_resp.status_code == 200, login_resp.text
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # must_change_password still true -- a require_full_access-gated route 403s.
    summary_resp = await client.get(
        "/api/v1/insurance-companies/me/dashboard-summary", headers=headers
    )
    assert summary_resp.status_code == 403, summary_resp.text
    # The ungated status check still works pre-full-access.
    get_resp = await client.get(f"/api/v1/insurance-companies/{company['id']}", headers=headers)
    assert get_resp.status_code == 200, get_resp.text
    assert get_resp.json()["status"] == "pending"

    change_resp = await client.patch(
        "/api/v1/auth/change-password",
        json={"current_password": otp, "new_password": "new-real-password-123"},
        headers=headers,
    )
    assert change_resp.status_code == 200, change_resp.text
    assert change_resp.json()["must_change_password"] is False
    assert change_resp.json()["org_approved"] is False
    headers = {"Authorization": f"Bearer {change_resp.json()['access_token']}"}

    # Password changed, but not yet approved -- still 403.
    summary_resp_2 = await client.get(
        "/api/v1/insurance-companies/me/dashboard-summary", headers=headers
    )
    assert summary_resp_2.status_code == 403, summary_resp_2.text

    approve_resp = await client.patch(
        f"/api/v1/admin/insurance-companies/{company['id']}/approve", headers=admin_headers
    )
    assert approve_resp.status_code == 200, approve_resp.text

    # Succeeds on the same still-valid token -- no re-login needed.
    summary_resp_3 = await client.get(
        "/api/v1/insurance-companies/me/dashboard-summary", headers=headers
    )
    assert summary_resp_3.status_code == 200, summary_resp_3.text


async def test_expired_otp_rejected_at_login(client: AsyncClient, db_session: AsyncSession) -> None:
    company, otp = await _onboard(
        client,
        name="Expired OTP Insurance",
        contact_email=f"admin-{uuid.uuid4()}@expired-otp-insurance.example.com",
    )
    user = await db_session.scalar(
        select(PlatformUser).where(PlatformUser.email == company["contact_email"])
    )
    assert user is not None
    user.otp_expires_at = datetime.now(UTC) - timedelta(hours=1)
    await db_session.flush()

    login_resp = await client.post(
        "/api/v1/auth/login", data={"username": company["contact_email"], "password": otp}
    )
    assert login_resp.status_code == 401, login_resp.text
    assert "expired" in login_resp.json()["detail"].lower()


async def test_reissue_otp_generates_working_new_code(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, otp = await _onboard(
        client,
        name="Reissue Insurance",
        contact_email=f"admin-{uuid.uuid4()}@reissue-insurance.example.com",
    )

    reissue_resp = await client.patch(
        f"/api/v1/admin/insurance-companies/{company['id']}/reissue-otp", headers=admin_headers
    )
    assert reissue_resp.status_code == 200, reissue_resp.text
    new_otp = reissue_resp.json()["otp"]
    assert new_otp != otp

    old_login = await client.post(
        "/api/v1/auth/login", data={"username": company["contact_email"], "password": otp}
    )
    assert old_login.status_code == 401, old_login.text

    new_login = await client.post(
        "/api/v1/auth/login", data={"username": company["contact_email"], "password": new_otp}
    )
    assert new_login.status_code == 200, new_login.text


async def test_change_password_rejects_wrong_current_password(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    company, otp = await _onboard(
        client,
        name="Wrong Password Insurance",
        contact_email=f"admin-{uuid.uuid4()}@wrong-password-insurance.example.com",
    )
    login_resp = await client.post(
        "/api/v1/auth/login", data={"username": company["contact_email"], "password": otp}
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    wrong_otp = f"{(int(otp) + 1) % 1_000_000:06d}"
    change_resp = await client.patch(
        "/api/v1/auth/change-password",
        json={"current_password": wrong_otp, "new_password": "whatever-new-123"},
        headers=headers,
    )
    assert change_resp.status_code == 401, change_resp.text
