from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "insureflow",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.tasks.installment_tasks",
        "app.workers.tasks.reminder_tasks",
        "app.workers.tasks.reconciliation_tasks",
    ],
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
celery_app.conf.beat_schedule = {
    "flag-overdue-installments-daily": {
        "task": "installments.flag_overdue",
        "schedule": crontab(hour=1, minute=0),
    },
    "top-up-installments-daily": {
        "task": "installments.top_up",
        "schedule": crontab(hour=1, minute=15),
    },
    "reconcile-transactions-every-30-minutes": {
        "task": "reconciliation.reconcile_transactions",
        "schedule": crontab(minute="*/30"),
    },
    "reconcile-transfers-every-30-minutes": {
        "task": "reconciliation.reconcile_transfers",
        "schedule": crontab(minute="*/30"),
    },
}
