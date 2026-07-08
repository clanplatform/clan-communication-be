from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "email-service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    PORT: int = 8001

    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/emails"
    REDIS_URL: str = "redis://localhost:6379/0"

    # SMTP relay (primary when enabled) — Gmail, Outlook, Mailgun, corporate, ...
    SMTP_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True    # STARTTLS (port 587)
    SMTP_USE_SSL: bool = False   # implicit TLS (port 465); overrides SMTP_USE_TLS

    # Default sender identity (used by all providers)
    SMTP_FROM_EMAIL: str = "noreply@example.com"
    SMTP_FROM_NAME: str = "Clan Platform"

    # SendGrid
    SENDGRID_API_KEY: str = ""
    SENDGRID_ENABLED: bool = False

    # AWS SES fallback
    AWS_SES_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_SES_ENABLED: bool = False

    # Notification service callback
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8000"

    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
