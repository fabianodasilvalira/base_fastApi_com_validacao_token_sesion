from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from loguru import logger

from app.core.session import get_db_session
from app.core.security import decode_token # Use the decode_token function from core.security
from app.core.config.settings import settings
from app.models.user import User
from app.schemas.auth import TokenData # Schema for token payload
from app.services import auth_service

# from app.services.user_service import user_service # Or use auth_service if it has get_user_by_id/email

# OAuth2PasswordBearer scheme
# This tells FastAPI that the token will be sent in the Authorization header
# as a Bearer token. The tokenUrl should point to your login endpoint.
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_current_user(
    db: AsyncSession = Depends(get_db_session),
    token: str = Depends(reusable_oauth2)
) -> User:
    """
    Dependency to get the current user from a JWT token.
    Raises HTTPException if the token is invalid, expired, or user not found/inactive.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    logger.debug(f"Attempting to get current user from token (first 8 chars): {token[:8]}...")
    
    token_data = decode_token(token) # Use the centralized decode_token function
    if not token_data or not token_data.email:
        logger.warning("Token decoding failed or email not in token payload.")
        raise credentials_exception
    
    # user = await user_service.get_user_by_email(db, email=token_data.email) # If using user_service
    user = await auth_service.get_user_by_email(db, email=token_data.email)
    if user is None:
        logger.warning(f"User {token_data.email} from token not found in database.")
        raise credentials_exception
    
    logger.info(f"Current user {user.email} identified successfully from token.")
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current active user.
    Checks if the user returned by get_current_user is active.
    """
    if not current_user.is_active:
        logger.warning(f"User {current_user.email} is inactive.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    logger.info(f"Current active user: {current_user.email}")
    return current_user

async def get_current_active_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to get the current active superuser.
    Checks if the user returned by get_current_active_user is a superuser.
    """
    if not current_user.is_superuser:
        logger.warning(f"User {current_user.email} is not a superuser. Access denied.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    logger.info(f"Current active superuser: {current_user.email}")
    return current_user

# How to use these dependencies in your API endpoints:
# from fastapi import APIRouter, Depends
# from app.api import deps
# from app.models.user import User
#
# router = APIRouter()
#
# @router.get("/users/me")
# async def read_users_me(current_user: User = Depends(deps.get_current_active_user)):
#     return current_user
#
# @router.post("/admin/some-action")
# async def admin_action(current_user: User = Depends(deps.get_current_active_superuser)):
#     # Only superusers can access this
#     return {"message": f"Admin action performed by {current_user.email}"}

# Onde modificar configurações relacionadas a dependências:
# - `reusable_oauth2`: O `tokenUrl` deve corresponder ao seu endpoint de login.
# - `decode_token`: A lógica de decodificação do token está em `app/core/security.py`.
#   As chaves e algoritmos são configurados em `app/core/config/security.py` (via `.env`).
# - A busca do usuário no banco de dados é feita usando `auth_service` (ou um `user_service` dedicado).

