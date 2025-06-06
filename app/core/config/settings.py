from functools import lru_cache
from app.core.config.base import BaseAppSettings
from pydantic import Field, HttpUrl, PostgresDsn, computed_field
from typing import List
from urllib.parse import quote_plus

class AppSettings(BaseAppSettings):
    # Gerais
    APP_ENV: str
    PROJECT_NAME: str
    API_V1_STR: str

    # Banco de Dados
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str

    @computed_field  # para Pydantic v2; se for v1 use @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{quote_plus(self.DB_USER)}:{quote_plus(self.DB_PASS)}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # Redis
    REDIS_URL: str 

    # Segurança
    ALGORITHM: str = "HS256"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # CORS
    BACKEND_CORS_ORIGINS: List[HttpUrl] = []

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "./logs/app.log"
    ERROR_LOG_FILE_PATH: str = "./logs/errors.log"
    LOG_ROTATION_SIZE: str = "10 MB"
    LOG_RETENTION_TIME: str = "7 days"

@lru_cache()
def get_settings():
    return AppSettings()

settings = get_settings()
