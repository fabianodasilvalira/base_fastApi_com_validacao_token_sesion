# app/models/__init__.py
from ..db.base import Base
from .user import User
from .cliente import Cliente
from .mesa import Mesa
from .comanda import Comanda
from .item_pedido import ItemPedido
from .produto import Produto
from .fiado import Fiado
from .pagamento import Pagamento
from .pedido import Pedido
from .item_pedido import ItemPedido
from .venda import Venda
from .venda_produto import VendaProduto



__all__ = ["Base", "User","Cliente", "Mesa", "Comanda", "ItemPedido", "Produto", "Fiado", "Pagamento", "Pedido", "ItemPedido", "Venda",
           "VendaProduto"]


