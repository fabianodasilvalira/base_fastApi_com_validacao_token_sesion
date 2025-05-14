from asyncio.log import logger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    auth,
    categoria,
    clientes,
    comandas,
    fiado,
    mesas,
    pagamentos,
    pedidos,
    produtos,
    relatorios,
    users,
    venda,
)
from app.core.config.settings import settings
from app.core.init_db import init_db
from app.core.logging.config import setup_logging
from app.core.session import AsyncSessionFactory

# Configura o logging da aplicação
setup_logging()

# Inicializa a aplicação FastAPI com informações para o Swagger
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para gerenciamento de barzinho, incluindo mesas, pedidos, comandas, produtos e relatórios.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Middleware de CORS para permitir requisições de outros domínios
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Evento executado na inicialização da aplicação
@app.on_event("startup")
async def startup_event():
    logger.info("Executando rotina de startup...")
    async with AsyncSessionFactory() as session:
        await init_db(session)

# Inclusão das rotas organizadas por grupo com tags para documentação Swagger
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Autenticação"])
app.include_router(categoria.router, prefix=f"{settings.API_V1_STR}/categoria", tags=["Categoria"])
app.include_router(clientes.router, prefix=f"{settings.API_V1_STR}/clientes", tags=["Clientes"])
app.include_router(comandas.router, prefix=f"{settings.API_V1_STR}/comandas", tags=["Comandas"])
app.include_router(fiado.router, prefix=f"{settings.API_V1_STR}/fiado", tags=["Fiado"])
app.include_router(mesas.router, prefix=f"{settings.API_V1_STR}/mesas", tags=["Mesas"])
app.include_router(pagamentos.router, prefix=f"{settings.API_V1_STR}/pagamentos", tags=["Pagamentos"])
app.include_router(pedidos.router, prefix=f"{settings.API_V1_STR}/pedidos", tags=["Pedidos"])
app.include_router(produtos.router, prefix=f"{settings.API_V1_STR}/produtos", tags=["Produtos"])
app.include_router(relatorios.router, prefix=f"{settings.API_V1_STR}/relatorios", tags=["Relatórios"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["Usuários"])
app.include_router(venda.router, prefix=f"{settings.API_V1_STR}/venda", tags=["Vendas"])
