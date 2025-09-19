from typing import List

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Messaging / RabbitMQ
    amqp_url: str = Field(default="amqp://guest:guest@localhost:5672/")

    # Storage service base URL
    storage_url: AnyHttpUrl = Field(default="http://localhost:8002")

    # API server
    cors_allowed_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://0.0.0.0:3000",
        ]
    )

    sse_ping_seconds: int = Field(default=15, ge=5, le=120)


def get_settings() -> Settings:
    # Cache settings instance to avoid re-parsing .env
    global _settings_instance
    try:
        return _settings_instance  # type: ignore[name-defined]
    except NameError:
        _settings_instance = Settings()
        return _settings_instance
