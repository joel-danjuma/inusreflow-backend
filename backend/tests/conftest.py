from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import engine, get_db
from app.core.deps import get_squad_client
from app.core.rate_limit import close_redis_client, get_redis_client
from app.main import app
from tests.fakes import FakeSquadClient


@pytest_asyncio.fixture(autouse=True)
async def _reset_rate_limit_state() -> AsyncGenerator[None, None]:
    """Rate-limit counters live in Redis, outside db_session's per-test
    rollback -- without this they'd persist across tests within the same
    fixed-window minute. This matters in particular because
    seed_and_activate_insureflow_admin logs in as the same fixed
    BOOTSTRAP_ADMIN_EMAIL in nearly every e2e test file; without a reset,
    enough tests running in one minute would trip enforce_login_rate_limit
    against each other. Scoped to the ratelimit: prefix only, not a full
    FLUSHDB, since Redis is also the Celery broker/backend.

    Always closes the client it creates, even for tests that never touch
    db_session (whose own teardown normally does this) -- otherwise a Redis
    client bound to this test's event loop leaks into the next test's
    different one (redis.asyncio connections aren't safe across loops).
    """
    redis = get_redis_client()
    try:
        keys = await redis.keys("ratelimit:*")
        if keys:
            await redis.delete(*keys)
        yield
    finally:
        await close_redis_client()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Binds a session to one connection-level transaction per test and rolls
    it back at the end, so tests can hit the real Postgres instance (per
    CLAUDE.md's testing strategy) without leaving data behind.
    """
    connection = await engine.connect()
    transaction = await connection.begin()
    session_factory = async_sessionmaker(bind=connection, expire_on_commit=False)
    session = session_factory()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_db, None)
        await session.close()
        await transaction.rollback()
        await connection.close()
        # Each test runs in its own event loop; asyncpg connections are not
        # safe to reuse across loops, so the pool must be torn down here too.
        await engine.dispose()
        await close_redis_client()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def fake_squad_client() -> AsyncGenerator[FakeSquadClient, None]:
    """Overrides get_squad_client so payment/webhook/settlement e2e tests never
    hit the real Squad sandbox -- outcomes are scripted via
    simulate_transaction()/set_payout_account() instead.
    """
    fake = FakeSquadClient()
    app.dependency_overrides[get_squad_client] = lambda: fake
    try:
        yield fake
    finally:
        app.dependency_overrides.pop(get_squad_client, None)
