from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Configuração do path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

# Importa configurações
from app.core.config.settings import settings

# Importa a Base única (apenas uma vez!)
from app.db.base import Base

# Importe TODOS os modelos aqui para que sejam registrados
from app.models import User, Cliente, Mesa, Comanda, ItemPedido, Produto, Fiado, Pagamento, Pedido, ItemPedido, Venda

# Adicione outros modelos conforme necessário

# Objeto de configuração do Alembic
config = context.config

# Configura o log
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadados para migrations
target_metadata = Base.metadata

def get_sync_url():
    """Converte a URL async para sync."""
    async_url = str(settings.DATABASE_URL)
    if "+asyncpg" in async_url:
        return async_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
    return async_url

def run_migrations_offline() -> None:
    """Executa migrations offline."""
    context.configure(
        url=get_sync_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Opcional: compara tipos de colunas
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Executa migrations online."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=get_sync_url(),  # Garante a URL síncrona
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Opcional: compara tipos de colunas
        )

        with context.begin_transaction():
            context.run_migrations()

# Executa as migrations
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()