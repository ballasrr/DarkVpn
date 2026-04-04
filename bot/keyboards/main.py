from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔑 Мой ключ", callback_data="my_key"),
            InlineKeyboardButton(text="📊 Статус", callback_data="status"),
        ],
        [
            InlineKeyboardButton(text="💳 Купить подписку", callback_data="buy"),
        ],
        [
            InlineKeyboardButton(text="📖 Инструкция", callback_data="guide"),
            InlineKeyboardButton(text="💬 Поддержка", callback_data="support"),
        ],
    ])


def plans_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1 месяц — 199₽", callback_data="plan_1m"),
        ],
        [
            InlineKeyboardButton(text="3 месяца — 499₽", callback_data="plan_3m"),
        ],
        [
            InlineKeyboardButton(text="1 год — 1499₽", callback_data="plan_1y"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back"),
        ],
    ])


def payment_kb(plan_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏦 Оплатить через СБП", callback_data=f"pay_sbp_{plan_key}"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="buy"),
        ],
    ])


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")],
    ])