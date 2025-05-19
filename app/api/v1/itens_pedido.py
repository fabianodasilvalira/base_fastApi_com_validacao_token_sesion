from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.session import get_db
from app.schemas.item_pedido_schemas import ItemPedidoCreate, ItemPedidoUpdate, ItemPedidoInResponse
from app.services.item_pedido_service import criar_item_pedido, atualizar_item_pedido, obter_item_pedido, obter_itens_pedido_por_comanda

router = APIRouter()

@router.post("/", response_model=ItemPedidoInResponse)
async def criar_item_pedido_api(
    item_pedido: ItemPedidoCreate,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Cria um novo item de pedido.
    """
    return await criar_item_pedido(db_session=db_session, item_pedido=item_pedido)

@router.put("/{item_pedido_id}", response_model=ItemPedidoInResponse)
async def atualizar_item_pedido_api(
    item_pedido_id: int,
    item_pedido: ItemPedidoUpdate,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Atualiza um item de pedido existente.
    """
    item_pedido_atualizado = await atualizar_item_pedido(
        db_session=db_session,
        item_pedido_id=item_pedido_id,
        item_pedido=item_pedido
    )
    if not item_pedido_atualizado:
        raise HTTPException(status_code=404, detail="Item de pedido não encontrado")
    return item_pedido_atualizado

@router.get("/{item_pedido_id}", response_model=ItemPedidoInResponse)
async def obter_item_pedido_api(
    item_pedido_id: int,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Obtém um item de pedido específico pelo ID.
    """
    item_pedido = await obter_item_pedido(db_session=db_session, item_pedido_id=item_pedido_id)
    if not item_pedido:
        raise HTTPException(status_code=404, detail="Item de pedido não encontrado")
    return item_pedido

@router.get("/comanda/{id_comanda}", response_model=List[ItemPedidoInResponse])
async def obter_itens_pedido_por_comanda_api(
    id_comanda: int,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Lista todos os itens de pedido associados a uma comanda específica.
    """
    itens_pedido = await obter_itens_pedido_por_comanda(db_session=db_session, id_comanda=id_comanda)
    return itens_pedido
