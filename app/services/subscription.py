import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import User, Subscription, Server, Plan, SubscriptionStatus
from app.core.marzban import marzban


class SubscriptionService:

    async def get_or_create_user(
        self,
        session: AsyncSession,
        telegram_id: int,
        username: str | None = None,
        full_name: str | None = None,
    ) -> User:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return user

    async def get_active_subscription(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> Subscription | None:
        result = await session.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.active,
            )
        )
        return result.scalar_one_or_none()

    async def create_trial(
        self,
        session: AsyncSession,
        user: User,
    ) -> Subscription:
        # выбираем активный сервер с наименьшей нагрузкой
        result = await session.execute(
            select(Server)
            .where(Server.is_active == True)
            .order_by(Server.load.asc())
            .limit(1)
        )
        server = result.scalar_one_or_none()
        if not server:
            raise ValueError("Нет доступных серверов")

        # создаём пользователя в Marzban
        marzban_username = f"dark_{user.telegram_id}"
        await marzban.create_user(
            username=marzban_username,
            days=3,
            traffic_gb=10,
        )
        vless_key = await marzban.get_user_key(marzban_username)

        # обновляем marzban_username у юзера
        user.marzban_username = marzban_username
        session.add(user)

        # создаём подписку
        subscription = Subscription(
            user_id=user.id,
            server_id=server.id,
            status=SubscriptionStatus.trial,
            vless_key=vless_key,
            expires_at=datetime.now() + timedelta(days=3),
        )
        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)

        return subscription

    async def activate(
        self,
        session: AsyncSession,
        user: User,
        plan: Plan,
    ) -> Subscription:
        # выбираем сервер
        result = await session.execute(
            select(Server)
            .where(Server.is_active == True)
            .order_by(Server.load.asc())
            .limit(1)
        )
        server = result.scalar_one_or_none()
        if not server:
            raise ValueError("Нет доступных серверов")

        marzban_username = user.marzban_username or f"dark_{user.telegram_id}"

        # продлеваем или создаём в Marzban
        try:
            await marzban.update_user(
                username=marzban_username,
                days=plan.duration_days,
                traffic_gb=plan.traffic_gb,
                status="active",
            )
        except Exception:
            await marzban.create_user(
                username=marzban_username,
                days=plan.duration_days,
                traffic_gb=plan.traffic_gb,
            )

        vless_key = await marzban.get_user_key(marzban_username)

        if user.marzban_username != marzban_username:
            user.marzban_username = marzban_username
            session.add(user)

        # деактивируем старую подписку если есть
        old = await self.get_active_subscription(session, user.id)
        if old:
            old.status = SubscriptionStatus.expired
            session.add(old)

        subscription = Subscription(
            user_id=user.id,
            server_id=server.id,
            plan_id=plan.id,
            status=SubscriptionStatus.active,
            vless_key=vless_key,
            expires_at=datetime.now() + timedelta(days=plan.duration_days),
        )
        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)

        return subscription

    async def expire_subscription(
        self,
        session: AsyncSession,
        subscription: Subscription,
    ) -> None:
        subscription.status = SubscriptionStatus.expired
        session.add(subscription)

        # отключаем в Marzban
        user = await session.get(User, subscription.user_id)
        if user and user.marzban_username:
            await marzban.disable_user(user.marzban_username)

        await session.commit()


subscription_service = SubscriptionService()