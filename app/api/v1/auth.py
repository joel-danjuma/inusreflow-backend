from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.auth import ActivateAccountRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    access_token = await auth_service.login(
        db, email=form_data.username, password=form_data.password
    )
    return TokenResponse(access_token=access_token)


@router.post("/activate", status_code=204)
async def activate(
    payload: ActivateAccountRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await auth_service.activate_account(db, token=payload.token, new_password=payload.password)
