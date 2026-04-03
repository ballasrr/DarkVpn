from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # Telegram
    BOT_TOKEN: str

    # Marzban
    MARZBAN_MASTER_URL: str
    MARZBAN_MASTER_USER: str
    MARZBAN_MASTER_PASS: str

    # Payments
    CRYPTOMUS_API_KEY: str
    CRYPTOMUS_MERCHANT_ID: str
    YUKASSA_SHOP_ID: str
    YUKASSA_SECRET_KEY: str

    # App
    SECRET_KEY: str
    DEBUG: bool = False


settings = Settings()