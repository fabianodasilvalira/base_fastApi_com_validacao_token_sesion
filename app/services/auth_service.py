from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from jose import jwt
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.models.token import RefreshToken
from app.models.user import User
from app.services.user_service import UserService


class AuthService:
    async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await UserService.get_user_by_email(db, email=email)

        if not user or not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: Invalid email or password for user {email}.")
            return None

        logger.info(f"User {email} authenticated successfully.")
        return user

    async def create_user_tokens(self, user_id: UUID, email: str) -> tuple[str, str]:
        """Generates new access and refresh tokens for a user."""
        access_token = create_access_token(data={"sub": email, "user_id": str(user_id)})
        refresh_token_str = create_refresh_token(data={"sub": email, "user_id": str(user_id)})
        logger.debug(f"Generated new tokens for user {email} (ID: {user_id})")
        return access_token, refresh_token_str

    async def store_refresh_token(self, db: AsyncSession, user_id: UUID, token_str: str) -> RefreshToken:
        try:
            decoded_jwt_payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            expires_at_timestamp = decoded_jwt_payload.get("exp")
            expires_at = datetime.fromtimestamp(expires_at_timestamp, tz=timezone.utc)

            db_refresh_token = RefreshToken(
                user_id=user_id,
                token=token_str,
                expires_at=expires_at.replace(tzinfo=None)  # remove tzinfo para evitar erro
            )
            db.add(db_refresh_token)
            await db.commit()
            await db.refresh(db_refresh_token)
            logger.info(f"Stored refresh token for user {user_id} (Token ID: {db_refresh_token.id})")
            return db_refresh_token
        except Exception as e:
            logger.error(f"Failed to store refresh token: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not process refresh token"
            )

    async def invalidate_refresh_token(self, db: AsyncSession, token_str: str) -> bool:
        """Invalidates/deletes a refresh token from the database."""
        try:
            stmt = select(RefreshToken).where(RefreshToken.token == token_str)
            result = await db.execute(stmt)
            db_refresh_token = result.scalars().first()

            if db_refresh_token:
                await db.delete(db_refresh_token)
                await db.commit()
                logger.info(f"Refresh token (ID: {db_refresh_token.id}) invalidated successfully.")
                return True
            logger.warning("Attempted to invalidate a refresh token that was not found.")
            return False
        except Exception as e:
            logger.error(f"Failed to invalidate refresh token: {str(e)}")
            await db.rollback()
            return False

    async def get_user_by_refresh_token(self, db: AsyncSession, token_str: str) -> Optional[User]:
        """Retrieves a user by their refresh token."""
        try:
            stmt = select(RefreshToken).where(RefreshToken.token == token_str)
            result = await db.execute(stmt)
            refresh_token = result.scalars().first()

            if not refresh_token or refresh_token.expires_at < datetime.now(timezone.utc):
                return None

            return await UserService.get_user_by_email(db, email=refresh_token.user.email)
        except Exception as e:
            logger.error(f"Error getting user by refresh token: {str(e)}")
            return None

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Busca o usuário pelo email usando o UserService."""
        return await UserService.get_user_by_email(db, email=email)

auth_service = AuthService()