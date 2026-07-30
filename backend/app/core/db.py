from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

#: Runtime queries connect as app_database_url's restricted, non-superuser
#: role -- not database_url's role, which Alembic uses and which owns the
#: tables -- so Postgres RLS policies actually apply (docs/adr/0006-row-level-security.md).
engine = create_async_engine(get_settings().app_database_url, pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
