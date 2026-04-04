from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Payment, PaymentStatus, User, Plan
from app.services.subscription import subscription_service

router = APIRouter(tags=["payments"])


@router.post("/webhook/cryptomus")
async def cryptomus_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    data = await request.json()

    # проверяем статус платежа
    if data.get("status") != "paid":
        return {"ok": True}

    provider_payment_id = data.get("uuid")
    if not provider_payment_id:
        return {"ok": True}

    # находим платёж в БД
    result = await session.execute(
        select(Payment).where(
            Payment.provider_payment_id == provider_payment_id
        )
    )
    payment = result.scalar_one_or_none()
    if not payment or payment.status == PaymentStatus.paid:
        return {"ok": True}

    # обновляем статус платежа
    payment.status = PaymentStatus.paid
    session.add(payment)

    # активируем подписку
    user = await session.get(User, payment.user_id)
    plan = await session.get(Plan, payment.subscription_id)

    if user and plan:
        await subscription_service.activate(session, user, plan)

    await session.commit()
    return {"ok": True}


@router.post("/webhook/yukassa")
async def yukassa_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    data = await request.json()

    if data.get("event") != "payment.succeeded":
        return {"ok": True}

    provider_payment_id = data["object"]["id"]

    result = await session.execute(
        select(Payment).where(
            Payment.provider_payment_id == provider_payment_id
        )
    )
    payment = result.scalar_one_or_none()
    if not payment or payment.status == PaymentStatus.paid:
        return {"ok": True}

    payment.status = PaymentStatus.paid
    session.add(payment)

    user = await session.get(User, payment.user_id)
    plan = await session.get(Plan, payment.subscription_id)

    if user and plan:
        await subscription_service.activate(session, user, plan)

    await session.commit()
    return {"ok": True}