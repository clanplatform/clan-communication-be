from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class SharedConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    REDIS_URL: str = "redis://localhost:6379/0"
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/comms"
    SECRET_KEY: str = "change-me-in-production"
    API_KEY_HEADER: str = "X-API-Key"

    EVENT_BUS_STREAM_MAX_LEN: int = 10_000
    EVENT_BUS_CONSUMER_GROUP: str = "notification-consumers"

    RATE_LIMIT_PER_TENANT_PER_MINUTE: int = 1000
    MAX_TENANTS: int = 1000


@lru_cache
def get_shared_config() -> SharedConfig:
    return SharedConfig()
