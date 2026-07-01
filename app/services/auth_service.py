from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    hash_activation_token,
    hash_password,
    verify_password,
)
from app.models.broker import Broker
from app.models.enums import OnboardingStatus
from app.models.insurance_company import InsuranceCompany
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Role


async def _resolve_org_status(db: AsyncSession, user: PlatformUser) -> str:
    role = Role(user.role)
    if role is Role.INSUREFLOW_ADMIN:
        return OnboardingStatus.APPROVED.value
    if role is Role.INSURANCE_COMPANY_ADMIN:
        company = await db.get(InsuranceCompany, user.insurance_company_id)
        return company.status if company is not None else OnboardingStatus.SUSPENDED.value
    broker = await db.get(Broker, user.broker_id)
    return broker.status if broker is not None else OnboardingStatus.SUSPENDED.value


async def login(db: AsyncSession, *, email: str, password: str) -> str:
    user = await db.scalar(select(PlatformUser).where(PlatformUser.email == email))
    if user is None or not user.is_active or user.hashed_password is None:
        raise AuthenticationError("invalid credentials")
    if not verify_password(password, user.hashed_password):
        raise AuthenticationError("invalid credentials")

    org_status = await _resolve_org_status(db, user)
    if org_status != OnboardingStatus.APPROVED.value:
        raise AuthenticationError("organization is not approved")

    role = Role(user.role)
    org_id = user.insurance_company_id if role is Role.INSURANCE_COMPANY_ADMIN else user.broker_id
    return create_access_token(user_id=user.id, role=role, org_id=org_id)


async def activate_account(db: AsyncSession, *, token: str, new_password: str) -> None:
    token_hash = hash_activation_token(token)
    user = await db.scalar(
        select(PlatformUser).where(PlatformUser.activation_token_hash == token_hash)
    )
    if user is None:
        raise AuthenticationError("invalid activation token")
    if user.activation_token_expires_at is None or user.activation_token_expires_at < datetime.now(
        UTC
    ):
        raise AuthenticationError("activation token expired")

    user.hashed_password = hash_password(new_password)
    user.is_active = True
    user.activation_token_hash = None
    user.activation_token_expires_at = None
    await db.flush()
