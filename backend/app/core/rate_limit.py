import time
from typing import Annotated

import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.core.metrics import rate_limit_rejections_total
from app.models.platform_user import PlatformUser

_logger = structlog.get_logger(__name__)

#: One process-wide client, not one per request -- redis-py's async Redis
#: pools connections internally, so this mirrors how the SQLAlchemy engine
#: in app/core/db.py is a single module-level instance too.
_redis_client: Redis | None = None

#: A fixed window is keyed by the current UTC minute, so the key itself
#: rolls over to a fresh counter every 60s with nothing to reset -- the TTL
#: below only exists so Redis reclaims the key's memory afterward, not for
#: correctness.
_WINDOW_SECONDS = 60
_KEY_TTL_SECONDS = 120


def get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(get_settings().redis_url, decode_responses=True)
    return _redis_client


async def close_redis_client() -> None:
    """Disposes the cached client -- mirrors app/core/db.py's engine.dispose()
    teardown. redis.asyncio's connection pool binds to the event loop it was
    first used on, so anything that outlives a single loop (e.g. each test
    function getting its own loop under pytest-asyncio) must be torn down
    and lazily recreated, never reused across loops.
    """
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


async def _check_and_increment(redis: Redis, key: str, limit: int, *, scope: str) -> None:
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, _KEY_TTL_SECONDS)
    if count > limit:
        rate_limit_rejections_total.labels(scope=scope).inc()
        _logger.warning("rate_limit.rejected", scope=scope, key=key, count=count, limit=limit)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded, try again shortly",
        )


async def enforce_payment_rate_limit(
    request: Request,
    actor: Annotated[PlatformUser, Depends(get_current_user)],
) -> None:
    """Fixed-window per-broker and per-IP limiter on payment-initiating
    endpoints (PRD §11.5). Both guards are independent and either one
    tripping is enough to reject -- a single broker can't buy more
    throughput by spraying requests across source IPs, and a shared NAT/
    proxy IP in front of several brokers isn't throttled just because one
    of them is over their own limit. This guards against runaway/abusive
    automation, not normal bulk broker workflows (CLAUDE.md) -- defaults
    are deliberately generous (Settings.payment_rate_limit_per_*).
    """
    settings = get_settings()
    redis = get_redis_client()
    window = int(time.time() // _WINDOW_SECONDS)

    if actor.broker_id is not None:
        await _check_and_increment(
            redis,
            f"ratelimit:broker:{actor.broker_id}:{window}",
            settings.payment_rate_limit_per_broker_per_minute,
            scope="broker",
        )

    client_host = request.client.host if request.client else "unknown"
    await _check_and_increment(
        redis,
        f"ratelimit:ip:{client_host}:{window}",
        settings.payment_rate_limit_per_ip_per_minute,
        scope="ip",
    )


async def enforce_login_rate_limit(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> None:
    """Fixed-window per-email and per-IP limiter on POST /auth/login. Added
    alongside the OTP onboarding flow: a 6-digit OTP has far less entropy
    than a full password, so login can no longer stay unthrottled the way it
    was when every credential was a real password. Keyed pre-authentication
    (the attempted email, not an authenticated actor), unlike
    enforce_payment_rate_limit.
    """
    settings = get_settings()
    redis = get_redis_client()
    window = int(time.time() // _WINDOW_SECONDS)

    await _check_and_increment(
        redis,
        f"ratelimit:login-email:{form_data.username.lower()}:{window}",
        settings.login_rate_limit_per_email_per_minute,
        scope="login_email",
    )

    client_host = request.client.host if request.client else "unknown"
    await _check_and_increment(
        redis,
        f"ratelimit:login-ip:{client_host}:{window}",
        settings.login_rate_limit_per_ip_per_minute,
        scope="login_ip",
    )
