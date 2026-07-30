"""Shared setup helpers for Phase 1 e2e/security tests.

Onboarding an org is a multi-step dance (onboard -> approve -> activate ->
login) that's identical across test files, so it's factored out here rather
than duplicated.
"""

from collections.abc import Mapping
from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_activation_token
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Role

BOOTSTRAP_ADMIN_EMAIL = "test-admin@insureflow.local"


async def _login(client: AsyncClient, *, email: str, password: str) -> dict[str, str]:
    login_resp = await client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def seed_and_activate_insureflow_admin(
    db_session: AsyncSession,
    client: AsyncClient,
    *,
    password: str = "admin-password-123",
) -> dict[str, str]:
    """Seeds a fresh Insureflow Admin directly (there's no API path to create
    the first one — that gap is filled in prod by a one-time migration-seeded
    admin instead), activates it through the real API, logs in, and returns
    auth headers.
    """
    raw_token, token_hash, expires_at = generate_activation_token()
    admin = PlatformUser(
        email=BOOTSTRAP_ADMIN_EMAIL,
        role=Role.INSUREFLOW_ADMIN.value,
        is_active=False,
        activation_token_hash=token_hash,
        activation_token_expires_at=expires_at,
    )
    db_session.add(admin)
    await db_session.flush()

    activate_resp = await client.post(
        "/api/v1/auth/activate", json={"token": raw_token, "password": password}
    )
    assert activate_resp.status_code == 204, activate_resp.text

    return await _login(client, email=BOOTSTRAP_ADMIN_EMAIL, password=password)


async def onboard_and_approve_insurance_company(
    client: AsyncClient,
    admin_headers: Mapping[str, str],
    *,
    name: str,
    contact_email: str,
    password: str = "company-admin-pw-123",
) -> tuple[dict[str, Any], dict[str, str]]:
    """Onboards an insurance company (capturing its OTP), logs in with it,
    sets a real password, then approves it as the given Insureflow Admin.
    Returns (company, admin_headers) for the company's own admin -- same
    shape as before, so every existing call site keeps working unmodified.
    """
    onboard_resp = await client.post(
        "/api/v1/insurance-companies", json={"name": name, "contact_email": contact_email}
    )
    assert onboard_resp.status_code == 201, onboard_resp.text
    body = onboard_resp.json()
    company, otp = body["company"], body["otp"]

    headers = await _login(client, email=contact_email, password=otp)

    change_resp = await client.patch(
        "/api/v1/auth/change-password",
        json={"current_password": otp, "new_password": password},
        headers=headers,
    )
    assert change_resp.status_code == 200, change_resp.text
    headers = {"Authorization": f"Bearer {change_resp.json()['access_token']}"}

    approve_resp = await client.patch(
        f"/api/v1/admin/insurance-companies/{company['id']}/approve", headers=admin_headers
    )
    assert approve_resp.status_code == 200, approve_resp.text

    get_resp = await client.get(f"/api/v1/insurance-companies/{company['id']}", headers=headers)
    assert get_resp.status_code == 200, get_resp.text
    return get_resp.json(), headers


async def onboard_and_approve_broker(
    client: AsyncClient,
    admin_headers: Mapping[str, str],
    *,
    name: str,
    contact_email: str,
    password: str = "broker-admin-pw-123",
    bvn: str = "22222222222",
    phone_number: str = "+2348012345678",
) -> tuple[dict[str, Any], dict[str, str]]:
    """Mirrors onboard_and_approve_insurance_company for brokers.

    bvn and phone_number are included so the approval flow creates a permanent
    Business SVA via FakeSquadClient (CLAUDE.md: one VA per broker at approval).
    The default bvn is a confirmed-valid Squad *sandbox* test BVN -- FakeSquadClient
    never validates it, but the handful of tests that exercise the real sandbox
    client (no fake_squad_client fixture) need a value Squad's own BVN check accepts.
    """
    onboard_resp = await client.post(
        "/api/v1/brokers",
        json={
            "name": name,
            "contact_email": contact_email,
            "bvn": bvn,
            "phone_number": phone_number,
        },
    )
    assert onboard_resp.status_code == 201, onboard_resp.text
    body = onboard_resp.json()
    broker, otp = body["broker"], body["otp"]

    headers = await _login(client, email=contact_email, password=otp)

    change_resp = await client.patch(
        "/api/v1/auth/change-password",
        json={"current_password": otp, "new_password": password},
        headers=headers,
    )
    assert change_resp.status_code == 200, change_resp.text
    headers = {"Authorization": f"Bearer {change_resp.json()['access_token']}"}

    approve_resp = await client.patch(
        f"/api/v1/admin/brokers/{broker['id']}/approve", headers=admin_headers
    )
    assert approve_resp.status_code == 200, approve_resp.text

    get_resp = await client.get(f"/api/v1/brokers/{broker['id']}", headers=headers)
    assert get_resp.status_code == 200, get_resp.text
    return get_resp.json(), headers


async def assign_broker_to_insurer(
    client: AsyncClient,
    admin_headers: Mapping[str, str],
    *,
    broker_id: str,
    insurance_company_id: str,
) -> None:
    resp = await client.post(
        f"/api/v1/admin/brokers/{broker_id}/assign-insurer",
        json={"insurance_company_id": insurance_company_id},
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text


async def unassign_broker_from_insurer(
    client: AsyncClient,
    admin_headers: Mapping[str, str],
    *,
    broker_id: str,
    insurance_company_id: str,
) -> None:
    resp = await client.delete(
        f"/api/v1/admin/brokers/{broker_id}/assign-insurer/{insurance_company_id}",
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text


async def create_policyholder(
    client: AsyncClient,
    company_headers: Mapping[str, str],
    *,
    broker_id: str,
    full_name: str = "Test Policyholder",
    email: str | None = None,
    phone_number: str | None = None,
    identification_number: str | None = None,
) -> dict[str, Any]:
    """Policyholder creation is insurer-only (many-to-many broker/insurer
    change) -- caller passes the acting insurer's own auth headers and
    names the broker this policyholder belongs to.
    """
    resp = await client.post(
        "/api/v1/users",
        json={
            "broker_id": broker_id,
            "full_name": full_name,
            "email": email,
            "phone_number": phone_number,
            "identification_number": identification_number,
        },
        headers=company_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def create_policy(
    client: AsyncClient,
    company_headers: Mapping[str, str],
    *,
    broker_id: str,
    policyholder_id: str,
    reference_number: str,
    premium_amount_kobo: int = 500_000,
    premium_frequency: str = "monthly",
    start_date: str = "2026-01-01",
    **extra: Any,
) -> dict[str, Any]:
    """Policy creation is insurer-only -- same shape as create_policyholder.
    reference_number must be unique per policy (a new required field).
    """
    payload: dict[str, Any] = {
        "broker_id": broker_id,
        "reference_number": reference_number,
        "policyholder_id": policyholder_id,
        "premium_amount_kobo": premium_amount_kobo,
        "premium_frequency": premium_frequency,
        "start_date": start_date,
        **extra,
    }
    resp = await client.post("/api/v1/policies", json=payload, headers=company_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()
