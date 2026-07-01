import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings
from app.rbac.permissions import Role

ACTIVATION_TOKEN_TTL = timedelta(days=7)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def create_access_token(*, user_id: uuid.UUID, role: Role, org_id: uuid.UUID | None) -> str:
    """org_id is insurance_company_id for INSURANCE_COMPANY_ADMIN, broker_id for
    BROKER_ADMIN/BROKER_STAFF, and None for INSUREFLOW_ADMIN. It is stable on the
    user record. For broker roles this is NOT the tenant id — the active
    insurance_company_id is resolved fresh per-request from
    broker_insurer_assignments, never cached here, so reassignment takes effect
    immediately (see app/core/deps.py get_tenant_id).
    """
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role.value,
        "org_id": str(org_id) if org_id else None,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def generate_activation_token() -> tuple[str, str, datetime]:
    """Returns (raw_token, token_hash, expires_at). The raw token is shown to the
    caller exactly once (it would be emailed in production); only its hash is
    persisted, mirroring how passwords are stored.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_activation_token(raw_token)
    expires_at = datetime.now(UTC) + ACTIVATION_TOKEN_TTL
    return raw_token, token_hash, expires_at


def hash_activation_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()
