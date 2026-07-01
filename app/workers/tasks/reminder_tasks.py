import asyncio
import uuid

from app.core.db import async_session_factory
from app.services import reminder_service
from app.workers.celery_app import celery_app


@celery_app.task(name="reminders.send_email")
def send_reminder_email_task(reminder_id: str) -> None:
    asyncio.run(_send(uuid.UUID(reminder_id)))


async def _send(reminder_id: uuid.UUID) -> None:
    async with async_session_factory() as db:
        await reminder_service.mark_reminder_sent(db, reminder_id=reminder_id)
        await db.commit()
