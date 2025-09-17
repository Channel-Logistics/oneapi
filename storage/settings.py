from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "oneapi-storage"
    APP_PORT: int = 9000
    DATABASE_URL: str = "postgresql+psycopg://app:app@postgres:5432/oneapi"
    # CORS / security toggles could go here later
    CORS_ORIGINS: List[str] | None = None
    model_config = {
        "env_file": ".env",  # optional, only if you use a local .env
        "case_sensitive": False,
    }


settings = Settings()
