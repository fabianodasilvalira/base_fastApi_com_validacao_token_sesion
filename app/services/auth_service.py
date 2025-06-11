import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

# Importe o novo modelo para o token de redefinição de senha
from app.models import RefreshToken, PasswordResetToken
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import (
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.core.config.settings import settings


class AuthService:
    REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
    # Define o tempo de expiração para o token de redefinição de senha (ex: 60 minutos)
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Busca usuário por email"""
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def create_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        """Cria um novo usuário"""
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            username=user_in.username,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            phone=user_in.phone,
            imagem_url=user_in.imagem_url,
            is_active=user_in.is_active if user_in.is_active is not None else True,
            is_superuser=user_in.is_superuser if user_in.is_superuser is not None else False,
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        logger.info(f"Usuário criado: {user_in.email} (ID: {db_user.id})")
        return db_user

    async def create_user_tokens(self, user_id: int, email: str) -> tuple[str, str]:
        """Cria tokens de acesso e refresh para o usuário"""
        access_token = create_access_token(data={"sub": email, "user_id": str(user_id)})
        refresh_token = create_refresh_token(data={"sub": email, "user_id": str(user_id)})
        return access_token, refresh_token

    async def store_refresh_token(self, db: AsyncSession, user_id: int, token_str: str) -> RefreshToken:
        """Armazena o refresh token no banco"""
        expires_at = (datetime.now(timezone.utc) + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)).replace(tzinfo=None)

        refresh_token = RefreshToken(
            user_id=user_id,
            token=token_str,
            expires_at=expires_at
        )

        db.add(refresh_token)
        await db.commit()
        await db.refresh(refresh_token)
        return refresh_token

    async def get_user_by_refresh_token(self, db: AsyncSession, token_str: str) -> Optional[User]:
        """Busca usuário pelo refresh token"""
        stmt = select(User).join(RefreshToken).where(
            RefreshToken.token == token_str,
            RefreshToken.expires_at > datetime.now(timezone.utc),
            RefreshToken.is_active == True
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def invalidate_refresh_token(self, db: AsyncSession, token_str: str) -> None:
        """Invalida um refresh token"""
        stmt = update(RefreshToken).where(
            RefreshToken.token == token_str
        ).values(is_active=False)

        await db.execute(stmt)
        await db.commit()

    # =========================================================================
    # ✅ NOVAS FUNÇÕES PARA REDEFINIÇÃO DE SENHA
    # =========================================================================

    async def create_password_reset_token(self, db: AsyncSession, user_id: int) -> str:
        """Cria e armazena um token de redefinição de senha."""
        # Gera um token seguro e aleatório
        token = secrets.token_urlsafe(32)

        # Define o tempo de expiração com fuso horário UTC
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=self.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )

        # Cria o objeto de token de redefinição
        reset_token_obj = PasswordResetToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at  # ✅ mantém timezone-aware
        )

        db.add(reset_token_obj)
        await db.commit()
        logger.info(f"Token de redefinição de senha criado para o usuário ID: {user_id}")
        return token



    async def get_user_by_password_reset_token(self, db: AsyncSession, token: str) -> Optional[User]:
        """Busca um usuário a partir de um token de redefinição de senha válido."""
        stmt = (
            select(User)
            .join(PasswordResetToken, User.id == PasswordResetToken.user_id)
            .where(
                PasswordResetToken.token == token,
                PasswordResetToken.expires_at > datetime.now(timezone.utc),
                PasswordResetToken.is_active == True
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def invalidate_password_reset_token(self, db: AsyncSession, token: str) -> None:
        """Invalida um token de redefinição de senha após o uso."""
        stmt = (
            update(PasswordResetToken)
            .where(PasswordResetToken.token == token)
            .values(is_active=False)
        )
        await db.execute(stmt)
        await db.commit()
        logger.info(f"Token de redefinição de senha invalidado: {token[:8]}...")


# Instância global do serviço
auth_service = AuthService()
