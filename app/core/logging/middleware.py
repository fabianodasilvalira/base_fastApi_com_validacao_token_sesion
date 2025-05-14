import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp
from loguru import logger
import uuid

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        
        # Log request details
        logger.info(
            f"Request ID: {request_id} - Started: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        # You can add more details like headers if needed, but be careful with sensitive info
        # logger.debug(f"Request ID: {request_id} - Headers: {dict(request.headers)}")

        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000  # milliseconds
            logger.info(
                f"Request ID: {request_id} - Finished: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Duration: {process_time:.2f}ms"
            )
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"Request ID: {request_id} - Exception: {request.method} {request.url.path} - "
                f"Error: {e} - Duration: {process_time:.2f}ms",
                exc_info=True # Adds traceback information
            )
            # Re-raise the exception to be handled by FastAPI's exception handlers or other middleware
            raise
        return response

# Como usar este middleware:
# No seu arquivo `main.py`, adicione:
# from app.core.logging.middleware import LoggingMiddleware
# app.add_middleware(LoggingMiddleware)
#
# Certifique-se de que esta linha seja adicionada APÓS a configuração do CORS middleware
# e, idealmente, como um dos primeiros middlewares para capturar o máximo de informações do request.

# Onde modificar configurações de Logging:
# - As configurações base (nível, caminhos de arquivo, rotação) são definidas em `.env`
#   e carregadas em `app/core/config/logging.py` -> `logging_settings`.
# - A configuração dos handlers e formatters do Loguru é feita em `app/core/logging/config.py`.
# - Este arquivo (`app/core/logging/middleware.py`) implementa o middleware para log de requisições.

