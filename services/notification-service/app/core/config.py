from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "notification-service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/notifications"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "change-me"
    API_KEY_HEADER: str = "X-API-Key"

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    EMAIL_SERVICE_URL: str = "http://email-service:8001"
    SMS_SERVICE_URL: str = "http://sms-service:8002"
    PUSH_SERVICE_URL: str = "http://push-notification-service:8003"
    IN_APP_SERVICE_URL: str = "http://in-app-notification-service:8004"
    WHATSAPP_SERVICE_URL: str = "http://whatsapp-service:8005"

    DEFAULT_TIMEZONE: str = "UTC"
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_BACKOFF_SECONDS: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
