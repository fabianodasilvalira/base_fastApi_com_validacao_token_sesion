from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.core.config.settings import settings
from app.services.user_service import user_service
from app.schemas.user import UserCreate  # Corrigido: o schema geralmente está em `schemas.user`
from app.models.user import User


async def init_db(db: AsyncSession) -> None:
    """Inicializa o banco de dados com dados necessários, como o superusuário."""
    logger.info("Inicializando o banco de dados...")

    # Verifica se as credenciais do superusuário estão configuradas
    if settings.FIRST_SUPERUSER and settings.FIRST_SUPERUSER_PASSWORD:
        # Tenta buscar o superusuário pelo email
        user = await user_service.get_user_by_email(db, email=settings.FIRST_SUPERUSER)

        if not user:
            # Cria o superusuário se não existir
            user_in = UserCreate(
                email=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                is_superuser=True,
                is_active=True
            )
            await user_service.create_user(db, user_in)
            logger.info(f"Superusuário {settings.FIRST_SUPERUSER} criado.")
        else:
            logger.info(f"Superusuário {settings.FIRST_SUPERUSER} já existe.")
    else:
        logger.warning("Configurações de superusuário ausentes. Criação ignorada.")

    logger.info("Processo de inicialização do banco concluído.")
