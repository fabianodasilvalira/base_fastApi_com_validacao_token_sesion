# app/db/session.py ou similar

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from app.core.config.settings import settings
from loguru import logger

# Criação do engine assíncrono
engine = create_async_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,
)

# Fábrica de sessões assíncronas
AsyncSessionFactory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@asynccontextmanager
async def get_db_session():
    session: AsyncSession = AsyncSessionFactory()
    try:
        logger.debug(f"DB Session {id(session)} created.")
        yield session
    except Exception as e:
        logger.error(f"DB Session {id(session)} error: {e}")
        await session.rollback()
        raise
    finally:
        logger.debug(f"DB Session {id(session)} closed.")
        await session.close()
