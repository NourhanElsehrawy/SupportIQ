from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SupportIQ API"
    environment: Literal["local", "test", "dev", "staging", "production"] = "local"
    database_url: str = "postgresql+psycopg://supportiq:supportiq@postgres:5432/supportiq"
    redis_url: str = "redis://redis:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
