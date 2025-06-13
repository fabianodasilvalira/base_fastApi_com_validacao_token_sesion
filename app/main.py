import logging

from fastapi import FastAPI, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordBearer

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
    venda, venda_produto_item, notifications,
)
from app.core.config.settings import settings
from app.core.logging.config import setup_logging
from app.services.user_service import create_first_superuser

logger = logging.getLogger(__name__)

# Configura o logging da aplicação
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para gerenciamento de barzinho, incluindo mesas, pedidos, comandas, produtos e relatórios.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# OAuth2 scheme para o Swagger usar no botão "Authorize"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

@app.on_event("startup")
async def on_startup():
    await create_first_superuser()

if settings.BACKEND_CORS_ORIGINS:
    try:
        origins = (
            json.loads(settings.BACKEND_CORS_ORIGINS)
            if isinstance(settings.BACKEND_CORS_ORIGINS, str)
            else settings.BACKEND_CORS_ORIGINS
        )
    except json.JSONDecodeError:
        origins = [settings.BACKEND_CORS_ORIGINS]

    print("🔵 CORS ORIGINS configurados:", origins)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Inclui suas rotas normalmente
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
app.include_router(venda_produto_item.router, prefix=f"{settings.API_V1_STR}/venda_produto_item", tags=["Produtos por Venda"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["Notificações"])


# Custom OpenAPI para incluir Bearer token no Swagger UI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="API para gerenciamento de barzinho, incluindo mesas, pedidos, comandas, produtos e relatórios.",
        routes=app.routes,
    )

    # Define o esquema de segurança Bearer JWT para Swagger
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # Aplica a segurança em todas as rotas (exceto a rota /login)
    for path, methods in openapi_schema["paths"].items():
        if f"{settings.API_V1_STR}/auth/login" not in path:
            for method in methods.values():
                method["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
