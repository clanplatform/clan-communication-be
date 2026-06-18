from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "in-app-notification-service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    PORT: int = 8004

    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/in_app"
    REDIS_URL: str = "redis://localhost:6379/0"

    WEBSOCKET_SERVICE_URL: str = "http://websocket-service:8006"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8000"

    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    UNREAD_BADGE_TTL_SECONDS: int = 3600


@lru_cache
def get_settings() -> Settings:
    return Settings()
