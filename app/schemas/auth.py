from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

class TokenRequest(BaseModel):
    email: str
    password: str

class TokenData(BaseModel):
    email: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenCreate(BaseModel):
    user_id: int
    token: str
    expires_at: datetime

class RefreshTokenInDB(RefreshTokenCreate):
    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str