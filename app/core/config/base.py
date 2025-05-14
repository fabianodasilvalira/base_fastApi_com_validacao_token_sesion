from pydantic_settings import BaseSettings

class BaseAppSettings(BaseSettings):
    class Config:
        env_file = ".env"
        extra = "ignore"
