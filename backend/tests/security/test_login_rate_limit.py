import uuid

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

import app.core.rate_limit as rate_limit
from app.core.config import get_settings


async def test_login_rate_limit_blocks_repeated_attempts_for_one_email(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Added alongside the OTP onboarding flow -- a 6-digit OTP is far more
    brute-forceable than a real password, so repeated failed attempts against
    one email must trip a limit before the underlying credential check ever
    gets a meaningful number of guesses.
    """
    low_limit_settings = get_settings().model_copy(
        update={"login_rate_limit_per_email_per_minute": 2}
    )
    monkeypatch.setattr(rate_limit, "get_settings", lambda: low_limit_settings)

    email = f"admin-{uuid.uuid4()}@login-rate-limit.example.com"

    def _attempt() -> object:
        return client.post("/api/v1/auth/login", data={"username": email, "password": "000000"})

    first = await _attempt()
    second = await _attempt()
    third = await _attempt()

    assert first.status_code == status.HTTP_401_UNAUTHORIZED, first.text
    assert second.status_code == status.HTTP_401_UNAUTHORIZED, second.text
    assert third.status_code == status.HTTP_429_TOO_MANY_REQUESTS, third.text


async def test_login_rate_limit_is_scoped_per_email(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second email exhausting its own limit must never affect the first --
    the counter key includes the attempted email, not just the endpoint/IP.
    """
    low_limit_settings = get_settings().model_copy(
        update={"login_rate_limit_per_email_per_minute": 1}
    )
    monkeypatch.setattr(rate_limit, "get_settings", lambda: low_limit_settings)

    email_a = f"a-{uuid.uuid4()}@login-rate-limit-scope.example.com"
    email_b = f"b-{uuid.uuid4()}@login-rate-limit-scope.example.com"

    a_first = await client.post(
        "/api/v1/auth/login", data={"username": email_a, "password": "000000"}
    )
    a_second = await client.post(
        "/api/v1/auth/login", data={"username": email_a, "password": "000000"}
    )
    b_first = await client.post(
        "/api/v1/auth/login", data={"username": email_b, "password": "000000"}
    )

    assert a_first.status_code == status.HTTP_401_UNAUTHORIZED, a_first.text
    assert a_second.status_code == status.HTTP_429_TOO_MANY_REQUESTS, a_second.text
    assert b_first.status_code == status.HTTP_401_UNAUTHORIZED, b_first.text
