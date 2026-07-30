import asyncio

from app.core.db import async_session_factory
from app.services import installment_service, policy_service
from app.workers.celery_app import celery_app


@celery_app.task(name="installments.flag_overdue")
def flag_overdue_installments_task() -> int:
    """Thin sync wrapper around the async service function — Celery tasks
    here are dispatch-only, never exercised by the (async) test suite, so
    there's no risk of nesting this asyncio.run() inside a running loop.
    """
    return asyncio.run(_flag_overdue())


async def _flag_overdue() -> int:
    async with async_session_factory() as db:
        count = await installment_service.flag_overdue_installments(db)
        await db.commit()
        return count


@celery_app.task(name="installments.top_up")
def top_up_installments_task() -> int:
    return asyncio.run(_top_up())


async def _top_up() -> int:
    async with async_session_factory() as db:
        count = await policy_service.top_up_all_active_policies(db)
        await db.commit()
        return count
