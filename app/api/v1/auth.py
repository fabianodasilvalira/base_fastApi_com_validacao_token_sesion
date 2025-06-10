from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.security import verify_password
from app.core.session import get_db
from app.schemas.auth import TokenResponse, RefreshTokenRequest, TokenRequest
from app.schemas.user import UserCreate, UserPublic # Certifique-se de que UserPublic está disponível
from app.services.auth_service import auth_service
from app.services.user_service import UserService
from app.core import deps # Importa suas dependências
from app.models.user import User # Importa o modelo de usuário

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="Autenticar usuário", tags=["Autenticação"])
async def fazer_login(
    response: Response,
    dados_login: TokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Autentica um usuário e retorna os tokens de acesso e refresh.

    - **email**: E-mail do usuário
    - **password**: Senha do usuário
    """
    try:
        logger.debug(f"Tentando login para: {dados_login.email}")

        usuario = await UserService.get_user_by_email(db, email=dados_login.email)
        if not usuario:
            logger.warning(f"Usuário {dados_login.email} não encontrado.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha incorretos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(dados_login.password, usuario.hashed_password):
            logger.warning(f"Senha incorreta para {usuario.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha incorretos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not usuario.is_active:
            logger.warning(f"Usuário inativo: {usuario.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuário inativo"
            )

        token_acesso, token_refresh = await auth_service.create_user_tokens(
            user_id=usuario.id,
            email=usuario.email
        )

        await auth_service.store_refresh_token(db, user_id=usuario.id, token_str=token_refresh)

        response.set_cookie(
            key="refresh_token",
            value=token_refresh,
            httponly=True,
            samesite="lax",
            secure=True, # Considere True apenas em produção com HTTPS
            max_age=30 * 24 * 60 * 60  # 30 dias
        )

        logger.info(f"Login bem-sucedido para {usuario.email}")
        return TokenResponse(
            access_token=token_acesso,
            refresh_token=token_refresh,
            token_type="bearer"
        )

    except HTTPException as e:
        logger.error(f"Erro HTTP durante login: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Erro inesperado durante login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno durante login"
        )


@router.post("/refresh-token", response_model=TokenResponse, summary="Atualizar token de acesso", tags=["Autenticação"])
async def atualizar_token_de_acesso(
        response: Response,
        dados: RefreshTokenRequest,
        db: AsyncSession = Depends(get_db)
):
    """
    Atualiza o token de acesso utilizando um token de refresh válido.

    Também gera um novo refresh token e substitui o anterior.
    """
    token_str = dados.refresh_token
    logger.info(f"Requisição de refresh token (início): {token_str[:8]}...")

    usuario = await auth_service.get_user_by_refresh_token(db, token_str=token_str)
    if not usuario:
        logger.warning("Refresh token inválido ou expirado.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de atualização inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    await auth_service.invalidate_refresh_token(db, token_str=token_str)

    novo_token_acesso, novo_token_refresh = await auth_service.create_user_tokens(
        user_id=usuario.id,
        email=usuario.email
    )

    await auth_service.store_refresh_token(db, user_id=usuario.id, token_str=novo_token_refresh)

    response.set_cookie(
        key="refresh_token",
        value=novo_token_refresh,
        httponly=True,
        samesite="lax",
        expires=auth_service.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    logger.info(f"Token atualizado com sucesso para {usuario.email}")
    return TokenResponse(
        access_token=novo_token_acesso,
        refresh_token=novo_token_refresh,
        token_type="bearer"
    )


@router.post("/logout", summary="Logout do usuário", tags=["Autenticação"])
async def deslogar_usuario(
        response: Response,
        db: AsyncSession = Depends(get_db),
):
    """
    Realiza o logout do usuário limpando o cookie de refresh token.
    """
    logger.info("Logout solicitado. Limpando cookie do refresh token.")
    response.delete_cookie(key="refresh_token", samesite="lax")
    return {"mensagem": "Logout realizado com sucesso"}


@router.post("/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED, summary="Cadastro de novo usuário", tags=["Autenticação"])
async def cadastrar_novo_usuario(
        dados_usuario: UserCreate,
        db: AsyncSession = Depends(get_db)
):
    """
    Cadastra um novo usuário no sistema.
    """
    logger.info(f"Tentativa de cadastro para o e-mail: {dados_usuario.email}")

    usuario_existente = await auth_service.get_user_by_email(db, email=dados_usuario.email)
    if usuario_existente:
        logger.warning(f"E-mail já cadastrado: {dados_usuario.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um usuário com este e-mail."
        )

    novo_usuario = await auth_service.create_user(db, user_in=dados_usuario)
    logger.info(f"Usuário criado com sucesso: {novo_usuario.email} (ID: {novo_usuario.id})")
    return novo_usuario

# --- Nova Rota: Obter informações do usuário atual ---
@router.get("/me", response_model=UserPublic, summary="Obter informações do usuário atual", tags=["Autenticação", "Usuários"])
async def get_usuario_atual(
    usuario_atual: User = Depends(deps.get_current_active_user) # Usa a dependência para obter o usuário logado
):
    """
    Retorna as informações públicas do usuário atualmente autenticado.

    **Requer autenticação com token de acesso.**
    """
    logger.info(f"Informações do usuário {usuario_atual.email} solicitadas.")
    return usuario_atual # O objeto 'usuario_atual' já é um modelo de Pydantic ou será convertido para UserPublic automaticamente