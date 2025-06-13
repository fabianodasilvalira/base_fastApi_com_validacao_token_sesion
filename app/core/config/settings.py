from functools import lru_cache
from pydantic import Field, AnyHttpUrl, computed_field
from pydantic_settings import BaseSettings
from typing import List, Optional, Union
from urllib.parse import quote_plus
from app.core.config.base import BaseAppSettings  # Supondo que esta classe exista
from pydantic import field_validator

class AppSettings(BaseAppSettings):
    # Gerais
    APP_ENV: str
    PROJECT_NAME: str
    API_V1_STR: str
    FRONTEND_URL: str

    # Banco de Dados
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    # Computed DATABASE_URL
    @computed_field
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{quote_plus(self.DB_USER)}:{quote_plus(self.DB_PASS)}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # Redis
    REDIS_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    SECRET_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int

    # Superusuário
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str

    # Email
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_FROM: Optional[str] = None
    MAIL_FROM_NAME: Optional[str] = None
    MAIL_PORT: int = 587
    MAIL_SERVER: Optional[str] = None
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    MAIL_STARTTLS: Optional[bool] = True
    MAIL_SSL_TLS: Optional[bool] = False

    # CORS
    BACKEND_CORS_ORIGINS: Union[str, List[AnyHttpUrl]] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def parse_cors(cls, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return [v.strip() for v in value.split(",")]
        return value

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "./logs/app.log"
    ERROR_LOG_FILE_PATH: str = "./logs/errors.log"
    LOG_ROTATION_SIZE: str = "10 MB"
    LOG_RETENTION_TIME: str = "7 days"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings():
    return AppSettings()

settings = get_settings()
