from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from loguru import logger

from app.core.session import get_db
from app.core.security import decode_token  # Use the decode_token function from core.security
from app.core.config.settings import settings
from app.models.user import User
from app.schemas.auth import TokenData  # Schema for token payload
# from app.services.auth_service import auth_service # Removido, pois usaremos user_service
from app.services.user_service import user_service  # Adicionado para usar user_service

# OAuth2PasswordBearer scheme
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_current_user(
        db: AsyncSession = Depends(get_db),
        token: str = Depends(reusable_oauth2)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    logger.debug(f"Attempting to get current user from token (first 8 chars): {token[:8]}...")

    token_data = decode_token(token)
    if not token_data or not token_data.email:
        logger.warning("Token decoding failed or email not in token payload.")
        raise credentials_exception

    user = await user_service.get_user_by_email(db=db, email=token_data.email)  # Alterado para user_service
    if user is None:
        logger.warning(f"User {token_data.email} from token not found in database.")
        raise credentials_exception

    logger.info(f"Current user {user.email} identified successfully from token.")
    return user


async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        logger.warning(f"User {current_user.email} is inactive.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    logger.info(f"Current active user: {current_user.email}")
    return current_user


async def get_current_active_superuser(
        current_user: User = Depends(get_current_active_user)
) -> User:
    if not current_user.is_superuser:
        logger.warning(f"User {current_user.email} is not a superuser. Access denied.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    logger.info(f"Current active superuser: {current_user.email}")
    return current_user

