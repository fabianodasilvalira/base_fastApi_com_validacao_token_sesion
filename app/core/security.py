from datetime import datetime, timedelta, timezone
from typing import Any, Union

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config.settings import settings
from app.schemas.auth import TokenData # Assuming TokenData schema is defined here
from loguru import logger

# Password hashing context using bcrypt
# bcrypt is a strong hashing algorithm recommended for passwords.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hashes a plain password.
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Creates a new JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Creates a new JWT refresh token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> TokenData | None:
    """
    Decodes a JWT token and returns its payload as TokenData.
    Returns None if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub") # Assuming "sub" (subject) is the user identifier (e.g., email)
        if email is None:
            logger.warning("Token decoding failed: subject (sub) missing in payload.")
            return None
        # You can add more validation here, e.g., check token type if you have different types
        # token_type: str | None = payload.get("type")
        # if token_type != "access": # Or whatever type you expect
        #     logger.warning(f"Invalid token type: {token_type}")
        #     return None
        return TokenData(email=email)
    except JWTError as e:
        logger.warning(f"Token decoding failed: {e}")
        return None

# Onde modificar configurações de Segurança:
# - Chaves e algoritmos: `app/core/config/security.py` (carregado do .env).
# - Duração dos tokens: `app/core/config/security.py` (carregado do .env).
# - Este arquivo (`app/core/security.py`) contém a lógica de hashing e JWT.

# Fluxo de Autenticação (reforçando):
# 1. Usuário envia credenciais.
# 2. `get_password_hash` é usado para criar hash de senha no registro.
# 3. `verify_password` é usado para verificar senha no login.
# 4. `create_access_token` e `create_refresh_token` são usados para gerar tokens após login bem-sucedido.
# 5. `decode_token` é usado em dependências (como `deps.get_current_user`) para validar tokens e extrair dados do usuário.

