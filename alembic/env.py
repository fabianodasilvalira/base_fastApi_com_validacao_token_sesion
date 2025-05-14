from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

import os
import sys

# Adiciona a raiz do projeto ao sys.path para permitir imports absolutos
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

# Importa configurações e modelos
from app.core.config.settings import settings
from app.models import user  # Garante que o modelo User seja registrado

# Importa a Base única usada por todos os modelos
from app.db.base import Base

# Objeto de configuração do Alembic
config = context.config

# Configura o log
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadados usados para autogeração de migrations
target_metadata = Base.metadata

# Retorna a URL síncrona para uso com o Alembic
def get_sync_url():
    return str(settings.DATABASE_URL).replace("postgresql+asyncpg", "postgresql+psycopg2")


def run_migrations_offline() -> None:
    """Executa as migrations no modo offline (sem conexão com o banco)."""
    url = get_sync_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa as migrations no modo online (conectado ao banco)."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_sync_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# Executa as migrations no modo adequado
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
