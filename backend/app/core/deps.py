import uuid
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import decode_access_token
from app.integrations.squad.client import HTTPSquadClient, SquadClient
from app.models.broker_insurer_assignment import BrokerInsurerAssignment
from app.models.enums import OnboardingStatus
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Permission, Role, role_has_permission
from app.services.auth_service import resolve_org_status

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlatformUser:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise credentials_error from exc

    user = await db.get(PlatformUser, user_id)
    if user is None or not user.is_active:
        raise credentials_error
    return user


async def require_full_access(
    user: Annotated[PlatformUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlatformUser:
    """Second gate beyond get_current_user's is_active check: a user can now
    hold a valid token while still mid-onboarding (OTP not yet changed, or
    org not yet approved -- see app/services/auth_service.py login). Every
    route that isn't part of that restricted-access surface (login,
    change-password, viewing own org status) goes through this instead of
    get_current_user directly -- require_permission, get_tenant_id, and
    get_own_insurer_id below all depend on this, not get_current_user.
    Re-derives both conditions fresh from the database on every request
    rather than trusting the JWT's own must_change_password/org_approved
    claims, which are UX-routing hints only (see create_access_token).
    """
    if user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Password change required"
        )
    if await resolve_org_status(db, user) != OnboardingStatus.APPROVED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Organization is not approved"
        )
    return user


async def _set_rls_context(
    db: AsyncSession, *, tenant_id: uuid.UUID | None, broker_id: uuid.UUID | None
) -> None:
    """Sets the two Postgres session GUCs the RLS policies in
    docs/adr/0006-row-level-security.md / docs/adr/0011-broker-insurer-many-to-many.md
    key off, for the rest of this request's DB transaction -- SET LOCAL so
    neither ever leaks onto a pooled connection's next, unrelated
    transaction. Both empty means cross-tenant (Insureflow Admin); a concrete
    tenant_id scopes an Insurance Company Admin to their own insurer; a
    concrete broker_id scopes a broker actor to their own rows across every
    insurer they work with. tenant_id and broker_id are never both set for
    the same request -- an actor is either insurer-side or broker-side, never
    both -- and app.current_tenant_id must never be set to a broker's
    dashboard-selected insurer (that narrowing stays a plain app-layer
    filter; feeding it into this GUC would leak other brokers' rows under
    the same insurer via the insurance_company_id branch of the policy).
    """
    # set_config(..., is_local=true), not a literal "SET LOCAL" statement --
    # SET doesn't accept bound parameters over asyncpg's extended query
    # protocol, but set_config() is an ordinary parameterizable SQL function.
    await db.execute(
        text(
            "SELECT set_config('app.current_tenant_id', :tenant_id, true), "
            "set_config('app.current_broker_id', :broker_id, true)"
        ),
        {
            "tenant_id": str(tenant_id) if tenant_id is not None else "",
            "broker_id": str(broker_id) if broker_id is not None else "",
        },
    )


async def get_tenant_id(
    user: Annotated[PlatformUser, Depends(require_full_access)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> uuid.UUID | None:
    """Sets this request's RLS context and returns the actor's own
    unambiguously-resolvable tenant id: None (cross-tenant) for Insureflow
    Admin, the company id directly for an Insurance Company Admin. For
    broker roles this is always None now -- a broker may have zero, one, or
    several active insurer assignments (many-to-many), so there is no single
    "my tenant" left to resolve here. Broker-side RLS scoping is instead
    carried by app.current_broker_id (see _set_rls_context), and reads that
    want narrowing to one specific counterparty use the explicit, validated
    get_broker_insurer_filter/get_insurer_broker_filter dependencies below --
    never a value silently picked by this function.
    """
    role = Role(user.role)
    if role is Role.INSUREFLOW_ADMIN:
        tenant_id, broker_id = None, None
    elif role is Role.INSURANCE_COMPANY_ADMIN:
        tenant_id, broker_id = user.insurance_company_id, None
    else:
        tenant_id, broker_id = None, user.broker_id

    await _set_rls_context(db, tenant_id=tenant_id, broker_id=broker_id)
    return tenant_id


async def get_own_insurer_id(
    user: Annotated[PlatformUser, Depends(require_full_access)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> uuid.UUID:
    """Insurer-dashboard equivalent of get_tenant_id, for routes that are
    never valid for a broker role at all. 403s any wrong role before
    touching the DB, rather than leaking an internal error for what is
    really just a permission failure.
    """
    if Role(user.role) is not Role.INSURANCE_COMPANY_ADMIN or user.insurance_company_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    await _set_rls_context(db, tenant_id=user.insurance_company_id, broker_id=None)
    return user.insurance_company_id


async def assert_broker_assigned_to_insurer(
    db: AsyncSession, *, insurer_id: uuid.UUID, broker_id: uuid.UUID
) -> None:
    """Shared validation: does this (broker, insurer) pair have a currently
    active assignment? Used both by get_insurer_broker_filter below (query
    -param narrowing) and directly by the policy/policyholder creation
    routes (request-body broker_id -- FastAPI dependencies can't read POST
    body fields the way they read query params, so those routes call this
    plain function instead of the Depends()-wrapped version). Raises 404,
    not 403 -- from an insurer's perspective an unassigned broker id is
    indistinguishable from a broker id that doesn't exist.
    """
    assignment = await db.scalar(
        select(BrokerInsurerAssignment).where(
            BrokerInsurerAssignment.broker_id == broker_id,
            BrokerInsurerAssignment.insurance_company_id == insurer_id,
            BrokerInsurerAssignment.is_active.is_(True),
        )
    )
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="broker not found")


async def get_broker_insurer_filter(
    user: Annotated[PlatformUser, Depends(require_full_access)],
    db: Annotated[AsyncSession, Depends(get_db)],
    insurer_id: Annotated[uuid.UUID | None, Query()] = None,
) -> uuid.UUID | None:
    """Broker-dashboard counterparty narrowing. None (the default -- no
    insurer_id passed) means aggregate across every currently-active insurer
    this broker works with. A concrete insurer_id must be one this broker is
    actively assigned to, or 404. This is a plain app-layer predicate for
    callers to lay on top of the broker_id RLS boundary get_tenant_id
    already set -- never a substitute for it, and never written back into
    app.current_tenant_id (see _set_rls_context's docstring for why).
    """
    if insurer_id is None:
        return None
    if Role(user.role) not in (Role.BROKER_ADMIN, Role.BROKER_STAFF) or user.broker_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    await assert_broker_assigned_to_insurer(db, insurer_id=insurer_id, broker_id=user.broker_id)
    return insurer_id


async def get_insurer_broker_filter(
    company_id: Annotated[uuid.UUID, Depends(get_own_insurer_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    broker_id: Annotated[uuid.UUID | None, Query()] = None,
) -> uuid.UUID | None:
    """Insurer-dashboard counterparty narrowing -- the mirror image of
    get_broker_insurer_filter. None means aggregate across every broker this
    insurer currently works with; a concrete broker_id must be one of them.
    """
    if broker_id is None:
        return None
    await assert_broker_assigned_to_insurer(db, insurer_id=company_id, broker_id=broker_id)
    return broker_id


def get_squad_client() -> SquadClient:
    """Overridden in tests (app.dependency_overrides) with FakeSquadClient --
    routes never import HTTPSquadClient directly so they stay testable.
    """
    settings = get_settings()
    return HTTPSquadClient(base_url=settings.squad_base_url, secret_key=settings.squad_secret_key)


def require_permission(
    permission: Permission,
) -> Callable[[PlatformUser], Coroutine[Any, Any, PlatformUser]]:
    async def checker(
        user: Annotated[PlatformUser, Depends(require_full_access)],
    ) -> PlatformUser:
        if not role_has_permission(Role(user.role), permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return checker
