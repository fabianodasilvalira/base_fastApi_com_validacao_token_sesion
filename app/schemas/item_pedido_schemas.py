# app/schemas/item_pedido.py
from pydantic import BaseModel, condecimal
from typing import Optional

class ItemPedidoBase(BaseModel):
    id_comanda: str
    id_produto: str
    quantidade: int = 1
    preco_unitario: condecimal(max_digits=10, decimal_places=2)
    preco_total: condecimal(max_digits=10, decimal_places=2)

class ItemPedidoCreate(ItemPedidoBase):
    pass

class ItemPedidoUpdate(ItemPedidoBase):
    pass

class ItemPedidoInResponse(ItemPedidoBase):
    id: str

    class Config:
        from_attributes = True
