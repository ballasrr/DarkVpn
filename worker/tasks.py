import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select

from worker.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.db.models import Subscription, SubscriptionStatus, Server, User
from app.core.marzban import marzban


def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="worker.tasks.check_expired_subscriptions")
def check_expired_subscriptions():
    return run_async(_check_expired_subscriptions())


async def _check_expired_subscriptions():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Subscription).where(
                Subscription.status == SubscriptionStatus.active,
                Subscription.expires_at <= datetime.now(),
            )
        )
        expired = result.scalars().all()

        for sub in expired:
            sub.status = SubscriptionStatus.expired
            session.add(sub)

            # отключаем в Marzban
            user = await session.get(User, sub.user_id)
            if user and user.marzban_username:
                try:
                    await marzban.disable_user(user.marzban_username)
                except Exception as e:
                    print(f"Ошибка отключения {user.marzban_username}: {e}")

            # уведомляем пользователя через бот
            if user:
                notify_user_expired.delay(user.telegram_id)

        await session.commit()
        print(f"Отключено истёкших подписок: {len(expired)}")


@celery_app.task(name="worker.tasks.send_expiry_reminders")
def send_expiry_reminders():
    return run_async(_send_expiry_reminders())


async def _send_expiry_reminders():
    async with AsyncSessionLocal() as session:
        # подписки которые истекают через 3 дня
        in_3_days = datetime.now() + timedelta(days=3)

        result = await session.execute(
            select(Subscription).where(
                Subscription.status == SubscriptionStatus.active,
                Subscription.expires_at <= in_3_days,
                Subscription.expires_at > datetime.now(),
                Subscription.notified_expiry == False,
            )
        )
        expiring = result.scalars().all()

        for sub in expiring:
            user = await session.get(User, sub.user_id)
            if user:
                days_left = (sub.expires_at - datetime.now()).days
                notify_user_expiring.delay(user.telegram_id, days_left)
                sub.notified_expiry = True
                session.add(sub)

        await session.commit()
        print(f"Отправлено напоминаний: {len(expiring)}")


@celery_app.task(name="worker.tasks.check_servers_health")
def check_servers_health():
    return run_async(_check_servers_health())


async def _check_servers_health():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Server))
        servers = result.scalars().all()

        for server in servers:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.get(f"{server.marzban_url}/api/system")
                    if resp.status_code == 200:
                        data = resp.json()
                        # обновляем нагрузку
                        mem = data.get("mem_used", 0)
                        mem_total = data.get("mem_total", 1)
                        server.load = int((mem / mem_total) * 100)
                        server.is_active = True
                    else:
                        server.is_active = False
            except Exception:
                server.is_active = False
                print(f"Сервер {server.name} недоступен")

            session.add(server)

        await session.commit()


@celery_app.task(name="worker.tasks.notify_user_expired")
def notify_user_expired(telegram_id: int):
    run_async(_notify_user_expired(telegram_id))


async def _notify_user_expired(telegram_id: int):
    from aiogram import Bot
    from app.core.config import settings

    bot = Bot(token=settings.BOT_TOKEN)
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=(
                "❌ <b>Подписка истекла</b>\n\n"
                "Твой VPN отключён.\n"
                "Продли подписку чтобы продолжить пользоваться DarkVPN."
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"Ошибка уведомления {telegram_id}: {e}")
    finally:
        await bot.session.close()


@celery_app.task(name="worker.tasks.notify_user_expiring")
def notify_user_expiring(telegram_id: int, days_left: int):
    run_async(_notify_user_expiring(telegram_id, days_left))


async def _notify_user_expiring(telegram_id: int, days_left: int):
    from aiogram import Bot
    from app.core.config import settings

    bot = Bot(token=settings.BOT_TOKEN)
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=(
                f"⚠️ <b>Подписка истекает через {days_left} дн.</b>\n\n"
                f"Не забудь продлить DarkVPN чтобы не потерять доступ."
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"Ошибка уведомления {telegram_id}: {e}")
    finally:
        await bot.session.close()