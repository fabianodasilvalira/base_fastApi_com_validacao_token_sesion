from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.core.config.settings import settings
from app.services.user_service import user_service, UserService
from app.schemas.user import UserCreate  # Corrigido: o schema geralmente está em `schemas.user`
from app.models.user import User


async def init_db(db: AsyncSession) -> None:
    # ...
    if settings.FIRST_SUPERUSER and settings.FIRST_SUPERUSER_PASSWORD:
        user = await UserService.get_user_by_email(db, email=settings.FIRST_SUPERUSER)

        if not user:
            user_in = UserCreate(
                email=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                is_superuser=True,
                is_active=True
            )
            await UserService.create_user(db, user_in)
            logger.info(f"Superusuário {settings.FIRST_SUPERUSER} criado.")
        else:
            logger.info(f"Superusuário {settings.FIRST_SUPERUSER} já existe.")
