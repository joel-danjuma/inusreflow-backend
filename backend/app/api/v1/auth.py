from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import enforce_login_rate_limit
from app.models.enums import OnboardingStatus
from app.models.platform_user import PlatformUser
from app.schemas.auth import ActivateAccountRequest, ChangePasswordRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login", response_model=TokenResponse, dependencies=[Depends(enforce_login_rate_limit)]
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    access_token, must_change_password, org_status = await auth_service.login(
        db, email=form_data.username, password=form_data.password
    )
    return TokenResponse(
        access_token=access_token,
        must_change_password=must_change_password,
        org_approved=(org_status == OnboardingStatus.APPROVED.value),
    )


@router.post("/activate", status_code=204)
async def activate(
    payload: ActivateAccountRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await auth_service.activate_account(db, token=payload.token, new_password=payload.password)


@router.patch("/change-password", response_model=TokenResponse)
async def change_password(
    payload: ChangePasswordRequest,
    user: Annotated[PlatformUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Depends on plain get_current_user, not require_full_access -- this
    must work precisely when must_change_password is still true.
    """
    access_token, must_change_password, org_status = await auth_service.change_password(
        db,
        user=user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return TokenResponse(
        access_token=access_token,
        must_change_password=must_change_password,
        org_approved=(org_status == OnboardingStatus.APPROVED.value),
    )
