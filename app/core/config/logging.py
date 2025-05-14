from app.core.config.base import BaseAppSettings

class LoggingSettings(BaseAppSettings):
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "./logs/app.log"
    ERROR_LOG_FILE_PATH: str = "./logs/errors.log"
    LOG_ROTATION_SIZE: str = "10 MB"
    LOG_RETENTION_TIME: str = "7 days"

    # Onde modificar configurações de Logging:
    # - As variáveis `LOG_LEVEL`, `LOG_FILE_PATH`, `ERROR_LOG_FILE_PATH`, `LOG_ROTATION_SIZE`, `LOG_RETENTION_TIME`
    #   são carregadas do arquivo `.env`.
    # - Este arquivo (`app/core/config/logging.py`) define o modelo Pydantic para essas configurações.
    # - A configuração real dos handlers e formatters do Loguru é feita em `app/core/logging/config.py`.
    # - Um middleware para log de requisições pode ser encontrado em `app/core/logging/middleware.py`.

    class Config:
        env_file = ".env"
        extra = "ignore"

logging_settings = LoggingSettings()

