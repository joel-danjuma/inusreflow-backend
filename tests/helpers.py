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
    """Onboards an insurance company, approves it as the given Insureflow
    Admin, activates its provisioned admin, and logs in. Returns
    (company, admin_headers) for the company's own admin.
    """
    onboard_resp = await client.post(
        "/api/v1/insurance-companies", json={"name": name, "contact_email": contact_email}
    )
    assert onboard_resp.status_code == 201, onboard_resp.text
    company = onboard_resp.json()

    approve_resp = await client.patch(
        f"/api/v1/admin/insurance-companies/{company['id']}/approve", headers=admin_headers
    )
    assert approve_resp.status_code == 200, approve_resp.text
    raw_token = approve_resp.json()["activation_token"]

    activate_resp = await client.post(
        "/api/v1/auth/activate", json={"token": raw_token, "password": password}
    )
    assert activate_resp.status_code == 204, activate_resp.text

    headers = await _login(client, email=contact_email, password=password)

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
) -> tuple[dict[str, Any], dict[str, str]]:
    """Mirrors onboard_and_approve_insurance_company for brokers."""
    onboard_resp = await client.post(
        "/api/v1/brokers", json={"name": name, "contact_email": contact_email}
    )
    assert onboard_resp.status_code == 201, onboard_resp.text
    broker = onboard_resp.json()

    approve_resp = await client.patch(
        f"/api/v1/admin/brokers/{broker['id']}/approve", headers=admin_headers
    )
    assert approve_resp.status_code == 200, approve_resp.text
    raw_token = approve_resp.json()["activation_token"]

    activate_resp = await client.post(
        "/api/v1/auth/activate", json={"token": raw_token, "password": password}
    )
    assert activate_resp.status_code == 204, activate_resp.text

    headers = await _login(client, email=contact_email, password=password)

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
