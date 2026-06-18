from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "push-notification-service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    PORT: int = 8003

    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/push"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Firebase Cloud Messaging
    FCM_SERVER_KEY: str = ""
    FCM_PROJECT_ID: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    FCM_ENABLED: bool = True

    # Apple Push Notification Service
    APNS_KEY_ID: str = ""
    APNS_AUTH_KEY: str = ""
    APNS_TEAM_ID: str = ""
    APNS_BUNDLE_ID: str = ""
    APNS_USE_SANDBOX: bool = False
    APNS_ENABLED: bool = False

    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
