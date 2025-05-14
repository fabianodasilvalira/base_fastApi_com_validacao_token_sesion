from asyncio.log import logger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, users # Placeholder, will be created later
from app.core.config.settings import settings
from app.core.init_db import init_db
from app.core.logging.config import setup_logging # Placeholder
from app.core.session import AsyncSessionFactory

# from app.core.logging.middleware import LoggingMiddleware # Placeholder

# Setup logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# app.add_middleware(LoggingMiddleware) # Add after creation

@app.get(f"{settings.API_V1_STR}/healthcheck", tags=["healthcheck"])
async def healthcheck():
    """
    Health check endpoint.
    """
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    logger.info("Executando rotina de startup...")
    async with AsyncSessionFactory() as session:
        await init_db(session)


app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])

