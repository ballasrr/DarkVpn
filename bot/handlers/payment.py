from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.keyboards.main import payment_kb, back_kb

router = Router()

PLANS = {
    "plan_1m": {"name": "1 месяц", "days": 30, "rub": 199, "usdt": 2.5},
    "plan_3m": {"name": "3 месяца", "days": 90, "rub": 499, "usdt": 6.0},
    "plan_1y": {"name": "1 год", "days": 365, "rub": 1499, "usdt": 18.0},
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
        f"🏦 <b>Оплата через СБП</b>\n\n"
        f"Тариф: <b>{plan['name']}</b>\n"
        f"Сумма: <b>{plan['rub']}₽</b>\n\n"
        f"⏳ Генерирую ссылку для оплаты...",
        reply_markup=back_kb(),
        parse_mode="HTML",
    )
    await callback.answer()