from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.session import get_db
from app.schemas.pedido_schemas import (
    PedidoCreate, StatusPedido, ItemPedido,
    ItemPedidoCreate, Pedido
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
    return await pedido_service.criar_pedido(db_session, pedido)

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
    return await pedido_service.listar_pedidos(
        db_session, status=status, data_inicio=data_inicio, data_fim=data_fim
    )

# Atualização do status do pedido
@router.put("/{pedido_id}/status", response_model=Pedido)
async def atualizar_status_pedido(
    pedido_id: int,
    status_update: StatusPedido,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Atualiza o status de um pedido.
    """
    pedido, mensagem = await pedido_service.atualizar_status_pedido(
        db_session, pedido_id, status_update
    )

    if pedido is None:
        raise HTTPException(status_code=400, detail=mensagem)

    return pedido

# Detalhar um pedido específico
@router.get("/{pedido_id}", response_model=Pedido)
async def detalhar_pedido(
    pedido_id: int,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Busca detalhes de um pedido específico.
    """
    pedido = await pedido_service.buscar_pedido(db_session, pedido_id)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado"
        )
    return pedido

# Adicionar item ao pedido
@router.post("/{pedido_id}/itens/", response_model=ItemPedido)
async def adicionar_item_pedido(
    pedido_id: int,
    item_in: ItemPedidoCreate,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Adiciona um novo item a um pedido existente.
    """
    item = await pedido_service.adicionar_item(db_session, pedido_id, item_in)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao adicionar item ao pedido"
        )
    return item

# Remover item do pedido
@router.delete("/{pedido_id}/itens/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_item_pedido(
    pedido_id: int,
    item_id: int,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Remove um item de um pedido.
    """
    sucesso = await pedido_service.remover_item(db_session, pedido_id, item_id)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao remover item do pedido"
        )
    return {"detail": "Item removido com sucesso"}

# Cancelar pedido
@router.put("/{pedido_id}/cancelar", response_model=Pedido)
async def cancelar_pedido(
    pedido_id: int,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Cancela um pedido e todos os seus itens.
    """
    pedido = await pedido_service.cancelar_pedido(db_session, pedido_id)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao cancelar o pedido"
        )
    return pedido

# Listar pedidos de um usuário específico
@router.get("/usuario/{usuario_id}", response_model=List[Pedido])
async def listar_pedidos_usuario(
    usuario_id: int,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Lista pedidos registrados por um usuário específico.
    """
    pedidos = await pedido_service.listar_pedidos_por_usuario(db_session, usuario_id)
    return pedidos
