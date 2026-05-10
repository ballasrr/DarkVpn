from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from app.db.session import AsyncSessionLocal
from app.services.subscription import subscription_service
from bot.keyboards.main import main_kb, plans_kb, back_kb

router = Router()


@router.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.edit_text(
        "🌑 <b>DarkVPN</b> — главное меню",
        reply_markup=main_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "my_key")
async def my_key(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        user = await subscription_service.get_or_create_user(
            session=session,
            telegram_id=callback.from_user.id,
        )
        sub = await subscription_service.get_active_subscription(
            session=session,
            user_id=user.id,
        )

    if not sub or not sub.vless_key:
        await callback.message.edit_text(
            "❌ У тебя нет активной подписки.\n\nКупи подписку чтобы получить ключ.",
            reply_markup=plans_kb(),
            parse_mode="HTML",
        )
        return

    await callback.message.edit_text(
        f"🔑 <b>Твой ключ подключения:</b>\n\n"
        f"<code>{sub.vless_key}</code>\n\n"
        f"📅 Действует до: <b>{sub.expires_at.strftime('%d.%m.%Y')}</b>\n\n"
        f"📖 Скопируй ключ и вставь в приложение <b>v2rayNG</b> (Android) "
        f"или <b>Streisand</b> (iOS)",
        reply_markup=back_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "status")
async def status(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        user = await subscription_service.get_or_create_user(
            session=session,
            telegram_id=callback.from_user.id,
        )
        sub = await subscription_service.get_active_subscription(
            session=session,
            user_id=user.id,
        )

    if not sub:
        await callback.message.edit_text(
            "❌ Активной подписки нет.",
            reply_markup=plans_kb(),
            parse_mode="HTML",
        )
        return

    days_left = (sub.expires_at - sub.expires_at.now()).days

    await callback.message.edit_text(
        f"📊 <b>Статус подписки</b>\n\n"
        f"✅ Статус: активна\n"
        f"📅 Истекает: <b>{sub.expires_at.strftime('%d.%m.%Y')}</b>\n"
        f"⏳ Осталось дней: <b>{days_left}</b>",
        reply_markup=back_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "buy")
async def buy(callback: CallbackQuery):
    await callback.message.edit_text(
        "💳 <b>Выбери тариф</b>\n\n"
        "🔹 <b>1 месяц</b> — 199₽ / 2.5 USDT\n"
        "🔹 <b>3 месяца</b> — 499₽ / 6 USDT\n"
        "🔹 <b>1 год</b> — 1499₽ / 18 USDT\n\n"
        "Все тарифы включают безлимитный трафик и доступ ко всем серверам.",
        reply_markup=plans_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "guide")
async def guide(callback: CallbackQuery):
    await callback.message.edit_text(
        "📖 <b>Как подключиться через Hiddify</b>\n\n"
        "1. Скачай приложение для своего устройства:\n\n"
        "📱 <b>iOS</b>\n"
        "<a href='https://apps.apple.com/app/hiddify-proxy-vpn/id6596777532'>Скачать Hiddify для iOS</a>\n\n"
        "🤖 <b>Android</b>\n"
        "<a href='https://play.google.com/store/apps/details?id=app.hiddify.com'>Скачать Hiddify для Android</a>\n\n"
        "🖥 <b>Windows</b>\n"
        "<a href='https://github.com/hiddify/hiddify-app/releases/latest/download/Hiddify-Windows-Setup-x64.exe'>Скачать Hiddify для Windows</a>\n\n"
        "🍎 <b>macOS</b>\n"
        "<a href='https://apps.apple.com/app/hiddify-proxy-vpn/id6596777532'>Скачать Hiddify для macOS</a>\n\n"
        "2. Открой приложение\n"
        "3. Нажми <b>+</b> → <b>Вставить из буфера обмена</b>\n"
        "4. Вставь свой ключ из раздела <b>🔑 Мой ключ</b>\n"
        "5. Нажми <b>Подключить</b>",
        reply_markup=back_kb(),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    await callback.answer()

@router.callback_query(F.data == "support")
async def support(callback: CallbackQuery):
    await callback.message.edit_text(
        "💬 <b>Поддержка DarkVPN</b>\n\n"
        "Если что-то не работает — напиши нам:\n"
        "@Ballas_RR\n\n"
        "Отвечаем в течение 24 часов.",
        reply_markup=back_kb(),
        parse_mode="HTML",
    )
    await callback.answer()