from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config.settings import settings
from loguru import logger

# Create an asynchronous engine instance.
# The engine is the starting point for any SQLAlchemy application.
# It's configured using the DATABASE_URL from our settings.
# echo=True would log all SQL statements, useful for debugging but can be verbose.
# future=True enables 2.0 style execution for SQLAlchemy 1.4+.
engine = create_async_engine(
    str(settings.DATABASE_URL), # SQLAlchemy expects a string URL
    pool_pre_ping=True, # Test connections before handing them out from the pool
    # echo=True, # Uncomment for debugging SQL queries
)

# Create an asynchronous session factory.
# AsyncSession is the main class used to interact with the database in an async way.
# expire_on_commit=False prevents attributes from being expired after commit,
# which can be useful if you need to access data after the session is committed.
AsyncSessionFactory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False, # Consider implications: default is True
    autocommit=False, # Default is False
)

async def get_db_session() -> AsyncSession:
    """
    Dependency to get a database session.

    This asynchronous generator will yield an AsyncSession instance.
    It ensures that the session is properly closed after the request is handled,
    even if an error occurs.
    """
    async_session = AsyncSessionFactory()
    try:
        logger.debug(f"DB Session {id(async_session)} created.")
        yield async_session
    except Exception as e:
        logger.error(f"DB Session {id(async_session)} error: {e}")
        await async_session.rollback() # Rollback in case of error
        raise
    finally:
        logger.debug(f"DB Session {id(async_session)} closed.")
        await async_session.close()

# Onde modificar configurações de Sessão/Banco de Dados:
# - `app/core/config/database.py` (e via `.env`): Define a URL do banco de dados (`DATABASE_URL`).
# - Este arquivo (`app/core/session.py`): Configura o engine SQLAlchemy e a fábrica de sessões.
# - `get_db_session`: É a dependência FastAPI que você injetará em suas rotas para obter uma sessão de banco de dados.

# Como usar `get_db_session` em suas rotas/serviços:
# from fastapi import APIRouter, Depends
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.core.session import get_db_session
#
# router = APIRouter()
#
# @router.get("/some-path")
# async def read_items(db: AsyncSession = Depends(get_db_session)):
#     # Use a sessão `db` aqui para interagir com o banco de dados
#     # result = await db.execute(select(MyModel).where(MyModel.id == 1))
#     # item = result.scalars().first()
#     return {"item": "data"}

# Para inicializar o banco de dados (criar tabelas):
# - Alembic é usado para gerenciar migrações de esquema (`alembic upgrade head`).
# - Um script `app/core/init_db.py` pode ser usado para popular dados iniciais (como um superusuário),
#   se necessário, após as tabelas serem criadas pelo Alembic.

