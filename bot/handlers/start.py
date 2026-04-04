from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.db.session import AsyncSessionLocal
from app.services.subscription import subscription_service
from bot.keyboards.main import main_kb

router = Router()

WELCOME_TEXT = """
🌑 <b>Добро пожаловать в DarkVPN</b>

Быстрый и надёжный VPN для обхода блокировок.

⚡️ Протокол VLESS+Reality — не блокируется
🌍 Серверы в Европе и США
📱 Работает на всех устройствах

Нажми <b>Купить подписку</b> чтобы начать.
Или получи <b>3 дня бесплатно</b> прямо сейчас!
"""


@router.message(CommandStart())
async def cmd_start(message: Message):
    async with AsyncSessionLocal() as session:
        user = await subscription_service.get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )

        # проверяем есть ли уже подписка
        sub = await subscription_service.get_active_subscription(
            session=session,
            user_id=user.id,
        )

        if sub:
            await message.answer(
                f"👋 С возвращением!\n\n"
                f"✅ Подписка активна до <b>{sub.expires_at.strftime('%d.%m.%Y')}</b>",
                reply_markup=main_kb(),
                parse_mode="HTML",
            )
        else:
            await message.answer(
                WELCOME_TEXT,
                reply_markup=main_kb(),
                parse_mode="HTML",
            )