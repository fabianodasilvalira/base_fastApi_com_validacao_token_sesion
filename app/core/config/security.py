from pydantic import Field, HttpUrl
from typing import List

class SecuritySettings:
    ALGORITHM: str = Field(default="HS256")
    SECRET_KEY: str = Field(default="super-secret-key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    BACKEND_CORS_ORIGINS: List[HttpUrl] = []

    class Config:
        env_file = ".env"
        extra = "ignore"
