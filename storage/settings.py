from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    app_name: str = "storage"
    database_url: str
    cors_origins: List[str] = []

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
