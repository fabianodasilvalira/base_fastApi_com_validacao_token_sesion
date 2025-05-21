from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.session import get_db
from app.schemas.item_pedido_schemas import (
    ItemPedidoCreate, ItemPedidoUpdate, ItemPedidoInResponse
)
from app.services.item_pedido_service import item_pedido_service

router = APIRouter()

# Adicionar item ao pedido
@router.post("/{pedido_id}/itens", response_model=ItemPedidoInResponse)
async def adicionar_item_pedido(
    pedido_id: int,
    item_in: ItemPedidoCreate,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Adiciona um novo item a um pedido existente.
    
    - **pedido_id**: ID do pedido ao qual o item será adicionado
    - **item_in**: Dados do item a ser adicionado
      - **id_produto**: ID do produto (obrigatório)
      - **quantidade**: Quantidade do produto (obrigatório, deve ser maior que zero)
      - **observacoes**: Observações sobre o item (opcional)
    
    O preço unitário será obtido automaticamente do produto no banco de dados.
    """
    item = await item_pedido_service.adicionar_item(db_session, pedido_id, item_in)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao adicionar item ao pedido"
        )
    return item

# Atualizar item do pedido
@router.put("/{pedido_id}/itens/{item_id}", response_model=ItemPedidoInResponse)
async def atualizar_item_pedido(
    pedido_id: int,
    item_id: int,
    item_update: ItemPedidoUpdate,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Atualiza um item de um pedido existente.
    
    - **pedido_id**: ID do pedido
    - **item_id**: ID do item a ser atualizado
    - **item_update**: Dados para atualização
      - **quantidade**: Nova quantidade (opcional, deve ser maior que zero)
      - **observacoes**: Novas observações (opcional)
    """
    item_atualizado = await item_pedido_service.atualizar_item(
        db_session, pedido_id, item_id, item_update
    )
    if not item_atualizado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item de pedido não encontrado ou não pertence ao pedido especificado"
        )
    return item_atualizado

# Remover item do pedido
@router.delete("/{pedido_id}/itens/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_item_pedido(
    pedido_id: int,
    item_id: int,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Remove um item de um pedido.
    
    - **pedido_id**: ID do pedido
    - **item_id**: ID do item a ser removido
    """
    sucesso = await item_pedido_service.remover_item(db_session, pedido_id, item_id)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao remover item do pedido"
        )
    return {"detail": "Item removido com sucesso"}

# Listar itens de um pedido
@router.get("/{pedido_id}/itens", response_model=List[ItemPedidoInResponse])
async def listar_itens_pedido(
    pedido_id: int,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Lista todos os itens de um pedido específico.
    
    - **pedido_id**: ID do pedido
    """
    itens = await item_pedido_service.listar_itens_por_pedido(db_session, pedido_id)
    return itens

# Obter detalhes de um item específico
@router.get("/{pedido_id}/itens/{item_id}", response_model=ItemPedidoInResponse)
async def obter_item_pedido(
    pedido_id: int,
    item_id: int,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Obtém detalhes de um item específico de um pedido.
    
    - **pedido_id**: ID do pedido
    - **item_id**: ID do item
    """
    item = await item_pedido_service.obter_item(db_session, pedido_id, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item de pedido não encontrado"
        )
    return item
