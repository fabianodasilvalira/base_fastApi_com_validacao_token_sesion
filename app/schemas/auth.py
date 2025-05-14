from pydantic import BaseModel, EmailStr

# Schema para o corpo da requisição de login
class TokenRequest(BaseModel):
    email: EmailStr
    password: str

# Schema para a resposta do token (incluindo o refresh token)
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str # O refresh token também é retornado
    token_type: str = "bearer"

# Schema para o corpo da requisição de refresh token
class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Schema para dados contidos no token JWT
class TokenData(BaseModel):
    email: EmailStr | None = None
    # Adicione outros campos que você queira incluir no token, se necessário

# Onde modificar configurações relacionadas à autenticação:
# - `app/core/config/security.py`: Contém configurações como SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES.
# - `app/services/auth_service.py`: Contém a lógica de autenticação, criação e verificação de tokens.
# - `.env` (ou `.env.example` para template): Define as variáveis de ambiente para as configurações de segurança.

# Fluxo de autenticação (reforçando o que foi dito em main.py):
# 1. Cliente envia POST para `/api/v1/auth/login` com `TokenRequest` (email, password).
# 2. O endpoint chama `auth_service.authenticate_user`.
# 3. Se as credenciais são válidas, `auth_service.create_access_token` e `auth_service.create_refresh_token` são chamados.
# 4. Uma `TokenResponse` é retornada ao cliente.
# 5. Para obter um novo access token, o cliente envia POST para `/api/v1/auth/refresh-token` com `RefreshTokenRequest`.
# 6. O endpoint valida o refresh token e, se válido, gera um novo access token e um novo refresh token (opcionalmente, invalidando o antigo).

