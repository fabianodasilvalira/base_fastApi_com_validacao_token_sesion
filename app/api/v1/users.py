from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.session import get_db
from app.schemas.user import UserPublic, UserUpdate, UserCreate
from app.models.user import User
from app.api import deps
from app.services.user_service import user_service
from app.core.security import get_password_hash

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuários"]
)

@router.post("/", response_model=UserPublic, status_code=status.HTTP_201_CREATED, summary="Criar novo usuário (admin)")
async def criar_usuario(
    usuario: UserCreate,
    db: AsyncSession = Depends(get_db),
    usuario_atual: User = Depends(deps.get_current_active_superuser)
):
    logger.info(f"Admin {usuario_atual.email} tentando criar o usuário: {usuario.email}")
    novo_usuario = await user_service.create_user(db=db, user_in=usuario)
    logger.info(f"Usuário {novo_usuario.email} criado com sucesso pelo admin {usuario_atual.email}.")
    return novo_usuario

@router.get("/me", response_model=UserPublic, summary="Obter informações do usuário logado")
async def obter_usuario_logado(
    usuario_atual: User = Depends(deps.get_current_active_user)
):
    logger.info(f"Buscando dados do usuário logado: {usuario_atual.email}")
    return usuario_atual

@router.get("/{usuario_id}", response_model=UserPublic, summary="Obter usuário por ID (admin)")
async def obter_usuario_por_id(
    usuario_id: int,  # Alterado de UUID para int
    db: AsyncSession = Depends(get_db),
    usuario_atual: User = Depends(deps.get_current_active_superuser)
):
    logger.info(f"Admin {usuario_atual.email} buscando usuário pelo ID: {usuario_id}")
    usuario = await user_service.get_user_by_id(db=db, user_id=usuario_id)
    if not usuario:
        logger.warning(f"Usuário com ID {usuario_id} não encontrado.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return usuario

@router.put("/{usuario_id}", response_model=UserPublic, summary="Atualizar dados de um usuário (admin)")
async def atualizar_usuario_por_id(
    usuario_id: int,  # Alterado de UUID para int
    dados_usuario: UserUpdate,
    db: AsyncSession = Depends(get_db),
    usuario_atual: User = Depends(deps.get_current_active_superuser)
):
    logger.info(f"Usuário {usuario_atual.email} tentando atualizar o usuário ID: {usuario_id}")
    usuario = await user_service.get_user_by_id(db=db, user_id=usuario_id)
    if not usuario:
        logger.warning(f"Usuário com ID {usuario_id} não encontrado para atualização.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    dados = dados_usuario.model_dump(exclude_unset=True)

    if "password" in dados and dados["password"]:
        usuario.hashed_password = get_password_hash(dados["password"])
        del dados["password"]

    for campo, valor in dados.items():
        setattr(usuario, campo, valor)

    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)

    logger.info(f"Usuário {usuario.email} (ID: {usuario_id}) atualizado com sucesso por {usuario_atual.email}.")
    return usuario
