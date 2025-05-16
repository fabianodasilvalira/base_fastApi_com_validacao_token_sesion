from pydantic import BaseModel, EmailStr
from typing import Optional


class TokenRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    email: Optional[EmailStr] = None
    user_id: Optional[str] = None  # Adicionado para facilitar lógica baseada no ID
