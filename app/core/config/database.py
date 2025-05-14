from pydantic import PostgresDsn, field_validator, ValidationInfo
from typing import Optional, Union

from app.core.config.base import BaseAppSettings

class DatabaseSettings(BaseAppSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASS: str = "password"
    DB_NAME: str = "fastapi_auth_db"

    # Asynchronous SQLAlchemy database URL
    # This will be constructed if not provided directly
    DATABASE_URL: Optional[PostgresDsn] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Union[str, PostgresDsn]:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=info.data.get("DB_USER"),
            password=info.data.get("DB_PASS"),
            host=info.data.get("DB_HOST"),
            port=info.data.get("DB_PORT"),
            path=f"{info.data.get('DB_NAME') or ''}",
        )

    # Onde modificar configurações do banco de dados:
    # - As variáveis `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, `DB_NAME` são carregadas do arquivo `.env`.
    # - `DATABASE_URL` é construída a partir dessas variáveis se não for fornecida diretamente no `.env`.
    #   Se `DATABASE_URL` estiver presente no `.env`, ela terá precedência.
    # - Este arquivo (`app/core/config/database.py`) define o modelo Pydantic para essas configurações.
    # - A conexão com o banco de dados é gerenciada em `app/core/session.py` usando SQLAlchemy.
    # - As migrações de banco de dados são gerenciadas pelo Alembic (configurado em `alembic.ini` e `alembic/env.py`).

    class Config:
        env_file = ".env"
        extra = "ignore"

db_settings = DatabaseSettings()

