import logging
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Payment, PaymentStatus, User, Plan
from app.services.subscription import subscription_service

router = APIRouter(tags=["payments"])
logger = logging.getLogger(__name__)

PLAN_MAP = {
    "plan_1m": {"duration_days": 30, "traffic_gb": 100},
    "plan_3m": {"duration_days": 90, "traffic_gb": 100},
    "plan_1y": {"duration_days": 365, "traffic_gb": 100},
}


@router.post("/webhook/yukassa")
async def yukassa_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    try:
        data = await request.json()
        logger.info(f"ЮKassa webhook: {data.get('event')}")

        if data.get("event") != "payment.succeeded":
            return {"ok": True}

        obj = data.get("object", {})
        provider_payment_id = obj.get("id")
        metadata = obj.get("metadata", {})
        plan_key = metadata.get("plan_key")
        user_telegram_id = metadata.get("user_id")

        if not provider_payment_id:
            return {"ok": True}

        result = await session.execute(
            select(Payment).where(
                Payment.provider_payment_id == provider_payment_id
            )
        )
        payment = result.scalar_one_or_none()

        if not payment:
            logger.warning(f"Платёж не найден: {provider_payment_id}")
            return {"ok": True}

        if payment.status == PaymentStatus.paid:
            return {"ok": True}

        payment.status = PaymentStatus.paid
        session.add(payment)

        user = await session.get(User, payment.user_id)
        if not user and user_telegram_id:
            result = await session.execute(
                select(User).where(User.telegram_id == int(user_telegram_id))
            )
            user = result.scalar_one_or_none()

        plan = None
        if plan_key:
            plan_data = PLAN_MAP.get(plan_key)
            if plan_data:
                result = await session.execute(
                    select(Plan).where(Plan.duration_days == plan_data["duration_days"])
                )
                plan = result.scalar_one_or_none()

        if user and plan:
            subscription = await subscription_service.activate(session, user, plan)
            logger.info(f"Подписка активирована для {user.telegram_id}")

            from aiogram import Bot
            from app.core.config import settings
            bot = Bot(token=settings.BOT_TOKEN)
            try:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=(
                        f"✅ <b>Оплата прошла успешно!</b>\n\n"
                        f"🔑 Твой ключ подключения:\n\n"
                        f"<code>{subscription.vless_key}</code>\n\n"
                        f"📖 Скопируй ключ и вставь в <b>Hiddify</b> или <b>v2rayNG</b>"
                    ),
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.error(f"Ошибка отправки ключа: {e}")
            finally:
                await bot.session.close()

        await session.commit()
        return {"ok": True}

    except Exception as e:
        logger.error(f"Ошибка webhook: {e}", exc_info=True)
        return {"ok": True}


@router.post("/webhook/cryptomus")
async def cryptomus_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    return {"ok": True}