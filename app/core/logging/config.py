import sys
from loguru import logger

from app.core.config.settings import settings

# Onde modificar configurações de Logging:
# - As configurações base (nível, caminhos de arquivo, rotação) são definidas em `.env`
#   e carregadas em `app/core/config/logging.py` -> `logging_settings`.
# - Este arquivo (`app/core/logging/config.py`) usa essas settings para configurar o Loguru.

def setup_logging():
    """
    Configures Loguru loggers based on the application settings.
    """
    logger.remove() # Remove default handler to avoid duplicate logs if re-configured.

    # Console logger (stdout)
    # Formato mais simples para console, com cores.
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL.upper(),
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # File logger for all logs (app.log)
    # Rotação de arquivo baseada em tamanho e retenção baseada em tempo.
    logger.add(
        settings.LOG_FILE_PATH,
        level=settings.LOG_LEVEL.upper(),
        rotation=settings.LOG_ROTATION_SIZE,
        retention=settings.LOG_RETENTION_TIME,
        enqueue=True,  # Asynchronous logging for performance
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8",
    )

    # File logger specifically for errors (errors.log)
    # Captura apenas logs de nível ERROR e CRITICAL.
    logger.add(
        settings.ERROR_LOG_FILE_PATH,
        level="ERROR",
        rotation=settings.LOG_ROTATION_SIZE,
        retention=settings.LOG_RETENTION_TIME,
        enqueue=True,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8",
    )

    logger.info(f"Logging setup complete. Level: {settings.LOG_LEVEL}, Main Log: {settings.LOG_FILE_PATH}")

# Como usar o logger em outras partes da aplicação:
# from loguru import logger
# logger.info("Esta é uma mensagem informativa.")
# logger.error("Ocorreu um erro!")
# logger.debug("Informação de debug.")

