from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "{{service-name}}"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    PORT: int = 8000

    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/{{service_db}}"
    REDIS_URL: str = "redis://localhost:6379/0"

    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
