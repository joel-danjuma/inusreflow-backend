import uuid
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import decode_access_token
from app.integrations.squad.client import HTTPSquadClient, SquadClient
from app.models.broker_insurer_assignment import BrokerInsurerAssignment
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Permission, Role, role_has_permission

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


async def _set_rls_tenant_context(db: AsyncSession, tenant_id: uuid.UUID | None) -> None:
    """Sets the Postgres session GUC the RLS policies in
    docs/adr/0006-row-level-security.md key off, for the rest of this
    request's DB transaction -- SET LOCAL so it never leaks onto a pooled
    connection's next, unrelated transaction. An empty string means
    cross-tenant (Insureflow Admin); a concrete UUID restricts every
    RLS-protected table's rows to that tenant as a second, database-level
    layer behind the existing app-layer scoping -- not a replacement for it.
    """
    # set_config(..., is_local=true), not a literal "SET LOCAL" statement --
    # SET doesn't accept bound parameters over asyncpg's extended query
    # protocol, but set_config() is an ordinary parameterizable SQL function.
    await db.execute(
        text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id) if tenant_id is not None else ""},
    )


async def get_tenant_id(
    user: Annotated[PlatformUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> uuid.UUID | None:
    """Cross-tenant (None) for Insureflow Admin, the company id directly for an
    Insurance Company Admin, and — for broker roles — resolved fresh from the
    broker's currently-active assignment, never cached on the JWT/user record.
    """
    role = Role(user.role)
    if role is Role.INSUREFLOW_ADMIN:
        tenant_id = None
    elif role is Role.INSURANCE_COMPANY_ADMIN:
        tenant_id = user.insurance_company_id
    else:
        stmt = select(BrokerInsurerAssignment).where(
            BrokerInsurerAssignment.broker_id == user.broker_id,
            BrokerInsurerAssignment.is_active.is_(True),
        )
        assignment = await db.scalar(stmt)
        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Broker has no active insurer assignment",
            )
        tenant_id = assignment.insurance_company_id

    await _set_rls_tenant_context(db, tenant_id)
    return tenant_id


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
        user: Annotated[PlatformUser, Depends(get_current_user)],
    ) -> PlatformUser:
        if not role_has_permission(Role(user.role), permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return checker
