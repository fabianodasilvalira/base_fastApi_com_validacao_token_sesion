# app/services/item_pedido.py
from sqlalchemy.orm import Session
from app.models.item_pedido import ItemPedido
from app.schemas.item_pedido import ItemPedidoCreate, ItemPedidoUpdate
from fastapi import HTTPException

def criar_item_pedido(db: Session, item_data: ItemPedidoCreate) -> ItemPedido:
    item = ItemPedido(
        id_comanda=item_data.id_comanda,
        id_produto=item_data.id_produto,
        quantidade=item_data.quantidade,
        preco_unitario=item_data.preco_unitario,
    )
    item.calcular_preco_total()
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def listar_itens_pedido(db: Session):
    return db.query(ItemPedido).all()

def obter_item_pedido(db: Session, item_id: int):
    item = db.query(ItemPedido).filter(ItemPedido.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return item

def atualizar_item_pedido(db: Session, item_id: int, item_update: ItemPedidoUpdate):
    item = obter_item_pedido(db, item_id)
    item.id_comanda = item_update.id_comanda
    item.id_produto = item_update.id_produto
    item.quantidade = item_update.quantidade
    item.preco_unitario = item_update.preco_unitario
    item.calcular_preco_total()
    db.commit()
    db.refresh(item)
    return item

def deletar_item_pedido(db: Session, item_id: int):
    item = obter_item_pedido(db, item_id)
    db.delete(item)
    db.commit()
    return {"detail": "Item excluído com sucesso"}
