from pydantic import BaseModel, root_validator
from enum import Enum
from typing import Optional, List
from decimal import Decimal
from uuid import UUID

# Enum para o status do pedido
class StatusPedido(str, Enum):
    RECEBIDO = "Recebido"
    EM_PREPARO = "Em Preparo"
    PRONTO_PARA_ENTREGA = "Pronto para Entrega"
    ENTREGUE_NA_MESA = "Entregue na Mesa"
    SAIU_PARA_ENTREGA_EXTERNA = "Saiu para Entrega (Externa)"
    ENTREGUE_CLIENTE_EXTERNO = "Entregue (Cliente Externo)"
    CANCELADO = "Cancelado"

# Enum para o tipo de pedido
class TipoPedido(str, Enum):
    INTERNO_MESA = "Interno (Mesa)"
    EXTERNO_DELIVERY = "Externo (Delivery)"
    EXTERNO_RETIRADA = "Externo (Retirada)"

# Schema para criação de itens no pedido
class ItemPedidoCreate(BaseModel):
    id_produto: int
    quantidade: int
    preco_unitario_no_momento: Decimal
    preco_total_item: Decimal
    observacoes_item: Optional[str] = None
    status_item_pedido: StatusPedido = StatusPedido.RECEBIDO

    # Validação para garantir que o preço total está correto
    @root_validator(pre=True)
    def validar_preco_total(cls, values):
        quantidade = values.get('quantidade')
        preco_unitario = values.get('preco_unitario_no_momento')
        preco_total_item = values.get('preco_total_item')

        if preco_total_item != (quantidade * preco_unitario):
            raise ValueError("O preço total do item não é consistente com a quantidade e o preço unitário.")
        return values

# Schema para itens do pedido (resposta)
class ItemPedido(ItemPedidoCreate):
    id: int
    status_item_pedido: StatusPedido

    class Config:
        from_attributes = True

# Schema para criação de um pedido
class PedidoCreate(BaseModel):
    id_comanda: int
    id_usuario_registrou: Optional[int] = None
    tipo_pedido: TipoPedido = TipoPedido.INTERNO_MESA
    status_geral_pedido: StatusPedido = StatusPedido.RECEBIDO
    observacoes_pedido: Optional[str] = None
    itens: List[ItemPedidoCreate]

# Schema de resposta do pedido
class Pedido(PedidoCreate):
    id: int
    itens: List[ItemPedido]

    class Config:
        from_attributes = True
