# app/models/__init__.py
from ..db.base import Base
from .cliente import Cliente
from .mesa import Mesa
from .comanda import Comanda
from .item_pedido import ItemPedido
from .produto import Produto


__all__ = ["Base", "Cliente", "Mesa", "Comanda", "ItemPedido", "Produto"]


