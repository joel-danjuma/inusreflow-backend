from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import engine, get_db
from app.core.deps import get_squad_client
from app.core.rate_limit import close_redis_client
from app.main import app
from tests.fakes import FakeSquadClient


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
