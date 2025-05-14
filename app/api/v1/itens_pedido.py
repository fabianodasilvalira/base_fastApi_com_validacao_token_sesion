# app/routers/item_pedido.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.session import get_db_session
from app.schemas.item_pedido_schemas import ItemPedidoCreate, ItemPedidoUpdate, ItemPedidoInResponse
from app.services.item_pedido import criar_item_pedido, atualizar_item_pedido, obter_item_pedido, obter_itens_pedido_por_comanda

router = APIRouter()

@router.post("/", response_model=ItemPedidoInResponse)
def criar_item_pedido_api(item_pedido: ItemPedidoCreate, db: Session = Depends(get_db_session())):
    return criar_item_pedido(db=db, item_pedido=item_pedido)

@router.put("/{item_pedido_id}", response_model=ItemPedidoInResponse)
def atualizar_item_pedido_api(item_pedido_id: str, item_pedido: ItemPedidoUpdate, db: Session = Depends(get_db_session)):
    item_pedido_atualizado = atualizar_item_pedido(db=db, item_pedido_id=item_pedido_id, item_pedido=item_pedido)
    if not item_pedido_atualizado:
        raise HTTPException(status_code=404, detail="ItemPedido não encontrado")
    return item_pedido_atualizado

@router.get("/{item_pedido_id}", response_model=ItemPedidoInResponse)
def obter_item_pedido_api(item_pedido_id: str, db: Session = Depends(get_db_session)):
    item_pedido = obter_item_pedido(db=db, item_pedido_id=item_pedido_id)
    if not item_pedido:
        raise HTTPException(status_code=404, detail="ItemPedido não encontrado")
    return item_pedido

@router.get("/comanda/{id_comanda}", response_model=list[ItemPedidoInResponse])
def obter_itens_pedido_por_comanda_api(id_comanda: str, db: Session = Depends(get_db_session)):
    itens_pedido = obter_itens_pedido_por_comanda(db=db, id_comanda=id_comanda)
    return itens_pedido
