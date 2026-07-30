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
from app.services.audit_service import record_audit_log


async def resolve_org_status(db: AsyncSession, user: PlatformUser) -> str:
    role = Role(user.role)
    if role is Role.INSUREFLOW_ADMIN:
        return OnboardingStatus.APPROVED.value
    if role is Role.INSURANCE_COMPANY_ADMIN:
        company = await db.get(InsuranceCompany, user.insurance_company_id)
        return company.status if company is not None else OnboardingStatus.SUSPENDED.value
    broker = await db.get(Broker, user.broker_id)
    return broker.status if broker is not None else OnboardingStatus.SUSPENDED.value


async def login(db: AsyncSession, *, email: str, password: str) -> tuple[str, bool, str]:
    """Returns (access_token, must_change_password, org_status). Login no
    longer requires org.status == approved outright -- a user can hold a
    valid OTP-derived password while their org is still pending (insurance
    company/broker onboarding) or while they're newly created staff. Full
    access is gated separately, per-request, by app/core/deps.py's
    require_full_access. Only a terminal rejected/suspended org still blocks
    login outright, preserving today's clear error for that case.
    """
    user = await db.scalar(select(PlatformUser).where(PlatformUser.email == email))
    if user is None or not user.is_active or user.hashed_password is None:
        raise AuthenticationError("invalid credentials")
    if not verify_password(password, user.hashed_password):
        raise AuthenticationError("invalid credentials")
    if (
        user.must_change_password
        and user.otp_expires_at is not None
        and user.otp_expires_at < datetime.now(UTC)
    ):
        raise AuthenticationError(
            "one-time password expired -- ask an Insureflow Admin to reissue it"
        )

    org_status = await resolve_org_status(db, user)
    if org_status in (OnboardingStatus.REJECTED.value, OnboardingStatus.SUSPENDED.value):
        raise AuthenticationError("organization is not approved")

    role = Role(user.role)
    org_id = user.insurance_company_id if role is Role.INSURANCE_COMPANY_ADMIN else user.broker_id
    access_token = create_access_token(
        user_id=user.id,
        role=role,
        org_id=org_id,
        must_change_password=user.must_change_password,
        org_approved=(org_status == OnboardingStatus.APPROVED.value),
    )
    return access_token, user.must_change_password, org_status


async def change_password(
    db: AsyncSession, *, user: PlatformUser, current_password: str, new_password: str
) -> tuple[str, bool, str]:
    """Sets a real password on first login (or any subsequent change),
    clearing must_change_password/otp_expires_at. Returns a fresh token
    (same shape as login) so the UX-hint claims are immediately correct
    without forcing a re-login.
    """
    if user.hashed_password is None or not verify_password(current_password, user.hashed_password):
        raise AuthenticationError("current password is incorrect")

    user.hashed_password = hash_password(new_password)
    user.must_change_password = False
    user.otp_expires_at = None
    await record_audit_log(
        db,
        action="platform_user.password_changed",
        entity_type="platform_user",
        entity_id=user.id,
        actor_id=user.id,
        actor_role=user.role,
    )
    await db.flush()

    org_status = await resolve_org_status(db, user)
    role = Role(user.role)
    org_id = user.insurance_company_id if role is Role.INSURANCE_COMPANY_ADMIN else user.broker_id
    access_token = create_access_token(
        user_id=user.id,
        role=role,
        org_id=org_id,
        must_change_password=False,
        org_approved=(org_status == OnboardingStatus.APPROVED.value),
    )
    return access_token, False, org_status


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
