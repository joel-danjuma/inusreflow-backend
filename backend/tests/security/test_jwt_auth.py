import uuid
from datetime import UTC, datetime, timedelta

import jwt
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Role
from tests.helpers import onboard_and_approve_insurance_company, seed_and_activate_insureflow_admin


def _make_token(
    *,
    user_id: uuid.UUID,
    role: Role = Role.INSUREFLOW_ADMIN,
    org_id: uuid.UUID | None = None,
    exp_delta: timedelta = timedelta(minutes=60),
    secret_key: str | None = None,
    algorithm: str | None = None,
) -> str:
    """Mirrors app.core.security.create_access_token's payload shape exactly,
    but takes exp_delta/secret_key/algorithm as direct overrides so tests can
    forge the one property under test (expiry, signing key) while leaving
    everything else identical to a real token -- a forgery attempt must be
    rejected even when it's otherwise indistinguishable from genuine.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "org_id": str(org_id) if org_id else None,
        "iat": now,
        "exp": now + exp_delta,
    }
    return jwt.encode(
        payload,
        secret_key if secret_key is not None else settings.jwt_secret_key,
        algorithm=algorithm or settings.jwt_algorithm,
    )


async def _seed_admin_and_company(
    client: AsyncClient, db_session: AsyncSession
) -> tuple[PlatformUser, str]:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name=f"JWT Test Co {uuid.uuid4()}",
        contact_email=f"admin-{uuid.uuid4()}@jwt-test.example.com",
    )
    admin = await db_session.scalar(
        select(PlatformUser).where(PlatformUser.role == Role.INSUREFLOW_ADMIN.value)
    )
    assert admin is not None
    return admin, company["id"]


async def test_expired_jwt_is_rejected(client: AsyncClient, db_session: AsyncSession) -> None:
    """A token whose exp claim is already in the past must be rejected even
    though it was signed with the real secret -- PyJWT's own expiry check
    inside decode_access_token, surfaced as 401 by get_current_user.
    """
    admin, company_id = await _seed_admin_and_company(client, db_session)
    expired_token = _make_token(user_id=admin.id, exp_delta=timedelta(minutes=-1))

    resp = await client.get(
        f"/api/v1/insurance-companies/{company_id}",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert resp.status_code == 401, resp.text


async def test_jwt_signed_with_an_unknown_secret_is_rejected(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A token an attacker forges without knowing jwt_secret_key must be
    rejected regardless of how plausible its claims look.
    """
    admin, company_id = await _seed_admin_and_company(client, db_session)
    forged_token = _make_token(user_id=admin.id, secret_key="attacker-does-not-know-this")

    resp = await client.get(
        f"/api/v1/insurance-companies/{company_id}",
        headers={"Authorization": f"Bearer {forged_token}"},
    )
    assert resp.status_code == 401, resp.text


async def test_jwt_for_a_never_activated_user_is_rejected(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A well-formed, correctly-signed token for a PlatformUser that's never
    completed activation (is_active=False, the model default) must still be
    rejected -- get_current_user's is_active gate, not just signature
    validity, decides whether a token grants access.
    """
    _, company_id = await _seed_admin_and_company(client, db_session)

    pending_user = PlatformUser(
        email=f"pending-{uuid.uuid4()}@example.com",
        role=Role.INSUREFLOW_ADMIN.value,
        is_active=False,
    )
    db_session.add(pending_user)
    await db_session.flush()

    token = _make_token(user_id=pending_user.id)

    resp = await client.get(
        f"/api/v1/insurance-companies/{company_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401, resp.text


async def test_jwt_with_a_malformed_subject_claim_is_rejected(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """sub must be a valid UUID -- get_current_user explicitly catches
    ValueError from uuid.UUID(...) alongside PyJWT's own errors, so a token
    with a garbage subject 401s instead of raising an unhandled exception.
    """
    _, company_id = await _seed_admin_and_company(client, db_session)
    settings = get_settings()
    now = datetime.now(UTC)
    bad_token = jwt.encode(
        {
            "sub": "not-a-uuid",
            "role": Role.INSUREFLOW_ADMIN.value,
            "org_id": None,
            "iat": now,
            "exp": now + timedelta(minutes=60),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    resp = await client.get(
        f"/api/v1/insurance-companies/{company_id}",
        headers={"Authorization": f"Bearer {bad_token}"},
    )
    assert resp.status_code == 401, resp.text
