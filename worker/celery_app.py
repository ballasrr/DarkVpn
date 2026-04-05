from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "darkvpn",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    timezone="Europe/Moscow",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    beat_schedule={
        # каждый час проверяем истёкшие подписки
        "check-expired-subscriptions": {
            "task": "worker.tasks.check_expired_subscriptions",
            "schedule": crontab(minute=0),
        },
        # каждый день в 10:00 шлём напоминания
        "send-expiry-reminders": {
            "task": "worker.tasks.send_expiry_reminders",
            "schedule": crontab(hour=10, minute=0),
        },
        # каждые 5 минут проверяем статус серверов
        "check-servers-health": {
            "task": "worker.tasks.check_servers_health",
            "schedule": crontab(minute="*/5"),
        },
    },
)