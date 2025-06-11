from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.config.settings import settings
from app.core.session import AsyncSessionFactory
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash


class UserService:
    """
    Classe de serviço para agrupar as operações relacionadas ao usuário.
    """
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Recupera um usuário pelo e-mail."""
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Recupera um usuário pelo ID."""
        logger.debug(f"Tentando recuperar usuário pelo ID: {user_id}")
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        if user:
            logger.info(f"Usuário com ID {user_id} encontrado: {user.email}")
        else:
            logger.warning(f"Usuário com ID {user_id} não encontrado.")
        return user

    @staticmethod
    async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
        """Cria um novo usuário no sistema."""
        logger.debug(f"Tentando criar usuário: {user_in.email}")
        existing_user = await UserService.get_user_by_email(db, email=user_in.email)
        if existing_user:
            logger.warning(f"Criação de usuário falhou: E-mail {user_in.email} já registrado.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O usuário com este e-mail já existe no sistema.",
            )

        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            is_active=user_in.is_active if user_in.is_active is not None else True,
            is_superuser=user_in.is_superuser if user_in.is_superuser is not None else False,
            username=user_in.username,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            phone=user_in.phone,
            imagem_url=user_in.imagem_url
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        logger.info(f"Usuário {user_in.email} criado com sucesso (ID: {db_user.id}).")
        return db_user

    @staticmethod
    async def update_password(db: AsyncSession, user: User, new_password: str) -> None:
        """
        Atualiza a senha de um usuário, garantindo que ela seja hasheada.
        """
        logger.info(f"Atualizando senha para o usuário: {user.email}")

        # Gera o hash da nova senha
        hashed_password = get_password_hash(new_password)

        # Atualiza o campo no objeto do usuário
        user.hashed_password = hashed_password

        # Adiciona o usuário à sessão e commita a alteração
        db.add(user)
        await db.commit()
        logger.info(f"Senha para {user.email} atualizada com sucesso.")


async def create_first_superuser():
    """
    Função para criar o primeiro superusuário do sistema durante a inicialização,
    se ele não existir.
    """
    async with AsyncSessionFactory() as session:
        try:
            result = await session.execute(
                select(User).where(User.email == settings.FIRST_SUPERUSER)
            )
            user = result.scalar_one_or_none()

            if user:
                logger.info("Superusuário já existe.")
                return

            superuser = User(
                email=settings.FIRST_SUPERUSER,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                is_active=True,
                is_superuser=True,
                first_name="Administrador",
                username="admin"
            )

            session.add(superuser)
            await session.commit()
            logger.info("Superusuário criado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao criar superusuário: {e}")


# Instância do serviço para ser importada e utilizada em outras partes da aplicação
user_service = UserService()
