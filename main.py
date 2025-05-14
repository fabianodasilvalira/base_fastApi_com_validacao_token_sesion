from asyncio.log import logger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, users, clientes, mesas, produtos, fiado, relatorios, \
    comandas, pedidos, pagamentos  # Placeholder, will be created later
from app.core.config.settings import settings
from app.core.init_db import init_db
from app.core.logging.config import setup_logging # Placeholder
from app.core.session import AsyncSessionFactory
from app.models import venda

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

@app.on_event("startup")
async def startup_event():
    logger.info("Executando rotina de startup...")
    async with AsyncSessionFactory() as session:
        await init_db(session)


app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(produtos.router, prefix=f"{settings.API_V1_STR}/produtos", tags=["Produtos"])
app.include_router(clientes.router, prefix=f"{settings.API_V1_STR}/clientes", tags=["Clientes"])
app.include_router(mesas.router, prefix=f"{settings.API_V1_STR}/mesas", tags=["Mesas"])
app.include_router(comandas.router, prefix=f"{settings.API_V1_STR}/comandas", tags=["Comandas"])
app.include_router(pedidos.router, prefix=f"{settings.API_V1_STR}/pedidos", tags=["Pedidos"])
app.include_router(pagamentos.router, prefix=f"{settings.API_V1_STR}/pagamentos", tags=["Pagamentos"])
app.include_router(fiado.router, prefix=f"{settings.API_V1_STR}/fiado", tags=["Fiado"])
app.include_router(relatorios.router, prefix=f"{settings.API_V1_STR}/relatorios", tags=["Relatórios"])
app.include_router(venda.router, prefix=f"{settings.API_V1_STR}/venda", tags=["Vendas"])

