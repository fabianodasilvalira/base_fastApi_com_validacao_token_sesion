import logging
from app.core.config.settings import settings
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from app.core.session import AsyncSessionFactory

logger = logging.getLogger(__name__)

async def create_first_superuser():
    async with AsyncSessionFactory() as session:
        # Verifica se já existe o superusuário
        result = await session.execute(
            User.select().where(User.email == settings.FIRST_SUPERUSER)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.info("Superusuário já existe.")
            return

        # Cria o superusuário
        superuser = User(
            nome="Administrador",
            email=settings.FIRST_SUPERUSER,
            hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            is_active=True,
            is_superuser=True
        )

        session.add(superuser)
        await session.commit()
        logger.info("Superusuário criado com sucesso.")
