from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm # For standard login form
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.session import get_db_session
from app.schemas.auth import TokenResponse, RefreshTokenRequest
from app.schemas.user import UserCreate, UserPublic # UserPublic for returning user info
from app.models.user import User # For type hinting current_user
from app.api import deps # For current_user dependency
from app.services import auth_service

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login_for_access_token(
    response: Response, # To set HTTPOnly cookie for refresh token
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Logs a user in and returns an access token and a refresh token.
    The refresh token is also set as an HTTPOnly cookie.
    Uses OAuth2PasswordRequestForm for standard username/password form body.
    """
    logger.info(f"Login attempt for user: {form_data.username}")
    user = await auth_service.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        logger.warning(f"Login failed: Invalid credentials for {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        logger.warning(f"Login failed: User {form_data.username} is inactive.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )

    access_token, refresh_token_str = await auth_service.create_user_tokens(user_id=user.id, email=user.email)
    await auth_service.store_refresh_token(db, user_id=user.id, token_str=refresh_token_str)

    # Set refresh token in an HTTPOnly cookie for better security
    response.set_cookie(
        key="refresh_token",
        value=refresh_token_str,
        httponly=True,
        samesite="lax", # or "strict"
        # secure=True, # Should be True in production (HTTPS)
        # domain="example.com", # Set your domain in production
        # path="/api/v1/auth", # Path where cookie is valid
        expires=auth_service.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60 # Expires in days
    )
    logger.info(f"User {form_data.username} logged in successfully. Access token and refresh token generated.")
    return TokenResponse(access_token=access_token, refresh_token=refresh_token_str, token_type="bearer")

@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_access_token(
    response: Response,
    refresh_request: RefreshTokenRequest, 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Refreshes an access token using a valid refresh token.
    A new refresh token is also generated and set as an HTTPOnly cookie, invalidating the old one.
    """
    token_str = refresh_request.refresh_token
    logger.info(f"Refresh token attempt with token (first 8 chars): {token_str[:8]}...")

    user = await auth_service.get_user_by_refresh_token(db, token_str=token_str)
    if not user:
        logger.warning("Refresh token failed: Invalid or expired refresh token.")
        # It's important not to leak whether the token existed or was just expired.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Invalidate the old refresh token
    await auth_service.invalidate_refresh_token(db, token_str=token_str)

    # Generate new pair of tokens
    new_access_token, new_refresh_token_str = await auth_service.create_user_tokens(user_id=user.id, email=user.email)
    await auth_service.store_refresh_token(db, user_id=user.id, token_str=new_refresh_token_str)

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token_str,
        httponly=True,
        samesite="lax",
        expires=auth_service.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    logger.info(f"Access token refreshed successfully for user {user.email}.")
    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token_str, token_type="bearer")

@router.post("/logout")
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    # current_user: User = Depends(deps.get_current_active_user) # Optional: ensure user is logged in to log out
    # If you want to invalidate a specific refresh token provided by client (e.g. from cookie implicitly)
    # you might need to read it from the request cookies if not sent in body.
    # For simplicity, this example assumes client discards tokens, and we clear the cookie.
):
    """
    Logs a user out.
    This basic version primarily clears the refresh_token cookie.
    A more robust version might invalidate the refresh token in the database if provided.
    """
    # If a refresh token is explicitly passed (e.g. from a secure cookie that the client can't read but server can process)
    # you could invalidate it here. For now, we just clear the cookie.
    # refresh_token_from_cookie = request.cookies.get("refresh_token")
    # if refresh_token_from_cookie:
    #     await auth_service.invalidate_refresh_token(db, token_str=refresh_token_from_cookie)

    logger.info(f"Logout attempt. Clearing refresh_token cookie.")
    response.delete_cookie(key="refresh_token", samesite="lax") # Ensure samesite matches what was set
    return {"message": "Logout successful"}


@router.post("/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def signup_new_user(
    user_in: UserCreate, 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Creates a new user.
    """
    logger.info(f"Signup attempt for email: {user_in.email}")
    existing_user = await auth_service.get_user_by_email(db, email=user_in.email)
    if existing_user:
        logger.warning(f"Signup failed: Email {user_in.email} already registered.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    
    # Ensure password and confirm_password match if confirm_password is part of UserCreate schema
    # if hasattr(user_in, 'confirm_password') and user_in.password != user_in.confirm_password:
    #     logger.warning(f"Signup failed for {user_in.email}: Passwords do not match.")
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Passwords do not match.",
    #     )

    created_user = await auth_service.create_user(db, user_in=user_in)
    logger.info(f"User {created_user.email} (ID: {created_user.id}) created successfully.")
    return created_user

# Como adicionar novas rotas de autenticação:
# 1. Defina a função da rota (ex: `async def reset_password(...)`).
# 2. Adicione o decorador `@router.post(...)` ou `@router.get(...)`.
# 3. Implemente a lógica, utilizando `auth_service` e `db` session.
# 4. Defina os schemas Pydantic para request body e response model.

# Fluxo de Autenticação (Endpoints):
# - `/login`: Recebe email/senha, retorna tokens (access e refresh), refresh token em cookie HTTPOnly.
# - `/refresh-token`: Recebe refresh token, retorna novos tokens, novo refresh token em cookie HTTPOnly.
# - `/logout`: Limpa o cookie do refresh token.
# - `/signup`: Cria um novo usuário.

