import asyncio
from datetime import timedelta

from app.core.config import get_settings
from app.core.db import async_session_factory
from app.core.deps import get_squad_client
from app.services import reconciliation_service
from app.workers.celery_app import celery_app


@celery_app.task(name="reconciliation.reconcile_transactions")
def reconcile_transactions_task() -> dict[str, int]:
    return asyncio.run(_reconcile_transactions())


async def _reconcile_transactions() -> dict[str, int]:
    settings = get_settings()
    squad_client = get_squad_client()
    async with async_session_factory() as db:
        result = await reconciliation_service.reconcile_transactions(
            db,
            squad_client=squad_client,
            merchant_id=settings.squad_merchant_id,
            stale_after=timedelta(minutes=settings.reconciliation_stale_after_minutes),
        )
        await db.commit()
        return {
            "payments_checked": result.payments_checked,
            "payments_resolved": result.payments_resolved,
            "batches_checked": result.batches_checked,
            "batches_resolved": result.batches_resolved,
        }


@celery_app.task(name="reconciliation.reconcile_transfers")
def reconcile_transfers_task() -> dict[str, int]:
    return asyncio.run(_reconcile_transfers())


async def _reconcile_transfers() -> dict[str, int]:
    settings = get_settings()
    squad_client = get_squad_client()
    async with async_session_factory() as db:
        result = await reconciliation_service.reconcile_transfers(
            db,
            squad_client=squad_client,
            page_size=settings.reconciliation_transfer_list_page_size,
        )
        await db.commit()
        return {
            "payouts_checked": result.payouts_checked,
            "payouts_resolved": result.payouts_resolved,
            "mismatches_flagged": result.mismatches_flagged,
        }
