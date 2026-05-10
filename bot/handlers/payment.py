import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from app.db.session import AsyncSessionLocal
from app.db.models import Payment, PaymentProvider, PaymentStatus
from app.services.subscription import subscription_service
from app.services.payment import yukassa
from bot.keyboards.main import payment_kb, back_kb

router = Router()
logger = logging.getLogger(__name__)

PLANS = {
    "plan_1m": {"name": "1 месяц", "days": 30, "rub": 199},
    "plan_3m": {"name": "3 месяца", "days": 90, "rub": 499},
    "plan_1y": {"name": "1 год", "days": 365, "rub": 1499},
}


@router.callback_query(F.data.startswith("plan_"))
async def choose_plan(callback: CallbackQuery):
    plan_key = callback.data
    plan = PLANS.get(plan_key)
    if not plan:
        await callback.answer("Неизвестный тариф")
        return

    await callback.message.edit_text(
        f"💳 <b>Тариф: {plan['name']}</b>\n\n"
        f"💰 Цена: <b>{plan['rub']}₽</b>\n\n"
        f"Выбери способ оплаты:",
        reply_markup=payment_kb(plan_key),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay_sbp_"))
async def pay_sbp(callback: CallbackQuery):
    plan_key = callback.data.replace("pay_sbp_", "")
    plan = PLANS.get(plan_key)
    if not plan:
        await callback.answer("Неизвестный тариф")
        return

    await callback.message.edit_text(
        "⏳ Генерирую ссылку для оплаты...",
        parse_mode="HTML",
    )

    try:
        async with AsyncSessionLocal() as session:
            user = await subscription_service.get_or_create_user(
                session=session,
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
            )

            pay_url, payment_id = await yukassa.create_sbp_payment(
                amount_rub=plan["rub"],
                plan_name=plan["name"],
                user_id=callback.from_user.id,
                plan_key=plan_key,
            )

            payment = Payment(
                user_id=user.id,
                amount=plan["rub"],
                currency="RUB",
                provider=PaymentProvider.yukassa,
                provider_payment_id=payment_id,
                status=PaymentStatus.pending,
            )
            session.add(payment)
            await session.commit()

        await callback.message.edit_text(
            f"🏦 <b>Оплата через СБП</b>\n\n"
            f"Тариф: <b>{plan['name']}</b>\n"
            f"Сумма: <b>{plan['rub']}₽</b>\n\n"
            f"👆 Нажми кнопку ниже для оплаты.\n"
            f"После оплаты ключ придёт автоматически.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏦 Перейти к оплате СБП", url=pay_url)],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy")],
            ]),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Ошибка оплаты: {e}", exc_info=True)
        await callback.message.edit_text(
            f"❌ Ошибка: {e}",
            reply_markup=back_kb(),
            parse_mode="HTML",
        )
    await callback.answer()