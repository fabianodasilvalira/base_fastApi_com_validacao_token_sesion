from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from app.core.session import get_db
from app.schemas.pedido_schemas import (
    PedidoCreate, StatusPedidoUpdate, Pedido, PedidoSemProduto
)
from app.services.pedido_service import pedido_service

router = APIRouter()

# Criação de um novo pedido
@router.post("/", response_model=Pedido, status_code=status.HTTP_201_CREATED)
async def criar_pedido(
    pedido: PedidoCreate,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Cria um novo pedido com seus itens associados.
    """
    pedido_dict = await pedido_service.criar_pedido(db_session, pedido)
    # Convertendo o dicionário para o schema Pedido para serialização segura
    return pedido_dict

# Listar pedidos (com filtros opcionais)
@router.get("/", response_model=List[Pedido])
async def listar_pedidos(
    db_session: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None
):
    """
    Lista pedidos com filtros opcionais.
    """
    pedidos_list = await pedido_service.listar_pedidos(
        db_session, status=status, data_inicio=data_inicio, data_fim=data_fim
    )
    return pedidos_list

# Atualização do status do pedido
@router.put("/{pedido_id}/status", response_model=PedidoSemProduto)
async def atualizar_status_pedido(
    pedido_id: int,
    status_update: StatusPedidoUpdate,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Atualiza o status de um pedido.
    """
    pedido_dict, mensagem = await pedido_service.atualizar_status_pedido(
        db_session, pedido_id, status_update.status
    )

    if pedido_dict is None:
        raise HTTPException(status_code=400, detail=mensagem)

    return pedido_dict

# Detalhar um pedido específico
@router.get("/{pedido_id}", response_model=Pedido)
async def detalhar_pedido(
    pedido_id: int,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Busca detalhes de um pedido específico.
    """
    pedido_dict = await pedido_service.buscar_pedido(db_session, pedido_id)
    return pedido_dict

# Cancelar pedido
@router.put("/{pedido_id}/cancelar", response_model=PedidoSemProduto)
async def cancelar_pedido(
    pedido_id: int,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Cancela um pedido e todos os seus itens.
    """
    pedido_dict = await pedido_service.cancelar_pedido(db_session, pedido_id)
    return pedido_dict

# Listar pedidos de um usuário específico
@router.get("/usuario/{usuario_id}", response_model=List[Pedido])
async def listar_pedidos_usuario(
    usuario_id: int,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Lista pedidos registrados por um usuário específico.
    """
    pedidos_list = await pedido_service.listar_pedidos_por_usuario(db_session, usuario_id)
    return pedidos_list
