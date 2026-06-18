from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "sms-service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    PORT: int = 8002

    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/sms"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Twilio
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""
    TWILIO_ENABLED: bool = True

    # AWS SNS fallback
    AWS_SNS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_SNS_ENABLED: bool = False

    # Vonage (Nexmo) fallback
    VONAGE_API_KEY: str = ""
    VONAGE_API_SECRET: str = ""
    VONAGE_FROM: str = "CLAN"
    VONAGE_ENABLED: bool = False

    MAX_SMS_LENGTH: int = 160
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
