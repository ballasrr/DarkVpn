import uuid
from yookassa import Configuration, Payment


class YookassaService:

    def __init__(self, shop_id: str, secret_key: str):
        Configuration.account_id = shop_id
        Configuration.secret_key = secret_key

    def create_sbp_payment(
        self,
        amount_rub: float,
        plan_name: str,
        user_id: int,
        plan_key: str,
    ) -> tuple[str, str]:
        payment = Payment.create({
            "amount": {
                "value": str(amount_rub),
                "currency": "RUB",
            },
            "payment_method_data": {
                "type": "sbp",
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/darkvpn5_bot",
            },
            "capture": True,
            "description": f"DarkVPN — {plan_name}",
            "metadata": {
                "user_id": str(user_id),
                "plan_key": plan_key,
            },
        }, str(uuid.uuid4()))

        pay_url = payment.confirmation.confirmation_url
        payment_id = payment.id
        return pay_url, payment_id


from app.core.config import settings
yukassa = YookassaService(
    shop_id=settings.YUKASSA_SHOP_ID,
    secret_key=settings.YUKASSA_SECRET_KEY,
)