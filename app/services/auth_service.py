import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from jose import jwt
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
from app.models.token import RefreshToken
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from app.services.user_service import UserService
logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        self.REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

    async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await UserService.get_user_by_email(db, email=email)
        if not user or not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed for {email}")
            return None
        logger.info(f"User {email} authenticated successfully.")
        return user

    async def create_user_tokens(self, user_id: UUID, email: str) -> tuple[str, str]:
        access_token = create_access_token(data={"sub": email, "user_id": str(user_id)})
        refresh_token = create_refresh_token(data={"sub": email, "user_id": str(user_id)})
        return access_token, refresh_token

    async def store_refresh_token(self, db: AsyncSession, user_id: str, token_str: str):
        try:
            logger.info(f"Armazenando refresh token para user_id {user_id}")
            expires_at = datetime.now(timezone.utc) + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
            # Converte para naive datetime (sem tzinfo)
            expires_at_naive = expires_at.replace(tzinfo=None)

            refresh_token = RefreshToken(
                user_id=user_id,
                token=token_str,
                expires_at=expires_at_naive
            )

            db.add(refresh_token)
            await db.commit()
            await db.refresh(refresh_token)
            logger.info(f"Refresh token armazenado com sucesso: {token_str[:8]}... (expira em {expires_at})")
        except Exception as e:
            logger.error(f"Erro ao armazenar refresh token: {e}")
            await db.rollback()
            raise

    async def invalidate_refresh_token(self, db: AsyncSession, token_str: str) -> bool:
        try:
            stmt = select(RefreshToken).where(RefreshToken.token == token_str)
            result = await db.execute(stmt)
            token = result.scalars().first()

            if token:
                await db.delete(token)
                await db.commit()
                logger.info(f"Refresh token {token.id} invalidated.")
                return True

            logger.warning("Refresh token not found for invalidation.")
            return False
        except Exception as e:
            logger.error(f"Error invalidating refresh token: {e}")
            await db.rollback()
            return False

    async def get_user_by_refresh_token(self, db: AsyncSession, token_str: str) -> Optional[User]:
        try:
            print("==== INÍCIO DA VERIFICAÇÃO DO REFRESH TOKEN ====")
            print(f"Token recebido na requisição (repr): {repr(token_str)}")
            print(f"Tipo do token_str: {type(token_str)}")

            # Garantir que não há espaços ou quebras de linha
            token_str = token_str.strip()
            print(f"Token após .strip(): {repr(token_str)}")

            # Busca com token comparado diretamente
            stmt = (
                select(RefreshToken)
                .options(selectinload(RefreshToken.user))
                .where(RefreshToken.token == token_str)
            )

            result = await db.execute(stmt)
            token = result.scalars().first()

            if not token:
                print("Token não encontrado no banco.")
                logger.warning(f"Refresh token não encontrado. token_str: {repr(token_str)}")
                return None

            print("==== TOKEN ENCONTRADO ====")
            print(f"Token do banco (repr): {repr(token.token)}")
            print(f"ID do token: {token.id}")
            print(f"ID do usuário: {token.user_id}")
            print(f"expires_at: {token.expires_at} (type: {type(token.expires_at)})")

            now = datetime.now(timezone.utc)
            print(f"Data atual (UTC): {now} (type: {type(now)})")

            expires_at_aware = token.expires_at
            if token.expires_at.tzinfo is None:
                expires_at_aware = token.expires_at.replace(tzinfo=timezone.utc)
                print(f"Token.expires_at convertido para timezone-aware: {expires_at_aware}")

            if expires_at_aware < now:
                print("==== TOKEN EXPIRADO ====")
                print(f"expires_at: {expires_at_aware}, now: {now}")
                logger.warning("Refresh token expirado.")
                return None

            print("==== TOKEN VÁLIDO ====")
            user = token.user
            if user:
                print(f"Usuário encontrado: {user.email} (ID: {user.id})")
            else:
                print("Usuário vinculado ao token não encontrado.")
            return user

        except Exception as e:
            print("==== ERRO NA VERIFICAÇÃO DO TOKEN ====")
            print(f"Erro: {e}")
            logger.error(f"Erro ao buscar usuário pelo refresh token: {e}")
            return None

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        return await UserService.get_user_by_email(db, email=email)

    async def create_user(self, db: AsyncSession, user_in: UserCreate) -> UserOut:
        # Verifica se o e-mail já está em uso
        existing_user = await UserService.get_user_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="E-mail já cadastrado."
            )

        hashed_password = get_password_hash(user_in.password)

        new_user = User(
        email=user_in.email,
        username=user_in.username,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        phone=user_in.phone,
        imagem_url=user_in.imagem_url,
        hashed_password=hashed_password,
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser,
        is_verified=False  # pode ser ajustado se necessário
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"Novo usuário criado: {new_user.email}")

        return UserOut.from_orm(new_user)


auth_service = AuthService()
