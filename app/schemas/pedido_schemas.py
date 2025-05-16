from pydantic import BaseModel, field_validator, model_validator
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
    preco_unitario: Decimal
    observacao: Optional[str] = None
    status_item_pedido: StatusPedido = StatusPedido.RECEBIDO

    @model_validator(mode='after')
    def calcular_preco_total(self) -> 'ItemPedidoCreate':
        self.preco_total_item = self.quantidade * self.preco_unitario
        return self

    class Config:
        from_attributes = True

# Schema para itens do pedido (resposta)
class ItemPedido(BaseModel):
    id: int
    id_produto: int
    quantidade: int
    preco_unitario: Decimal
    preco_total_item: Decimal
    observacao: Optional[str] = None
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

    class Config:
        from_attributes = True

# Schema de resposta do pedido
class Pedido(BaseModel):
    id: int
    id_comanda: int
    id_usuario_registrou: Optional[int] = None
    tipo_pedido: TipoPedido
    status_geral_pedido: StatusPedido
    observacoes_pedido: Optional[str] = None
    itens: List[ItemPedido]

    class Config:
        from_attributes = True

# Schemas para interface pública (QRCode)
class ItemPedidoPublicCreateSchema(BaseModel):
    produto_id: int
    quantidade: int
    observacao: Optional[str] = None

class PedidoPublicCreateSchema(BaseModel):
    itens: List[ItemPedidoPublicCreateSchema]

class ItemPedidoPublicResponseSchema(BaseModel):
    produto_nome: str
    quantidade: int
    preco_unitario: Decimal
    preco_total_item: Decimal
    observacao: Optional[str] = None

class PedidoPublicResponseSchema(BaseModel):
    id_comanda: str
    status_comanda: str
    mesa_numero: Optional[str] = None
    itens_confirmados: List[ItemPedidoPublicResponseSchema]
    valor_total_comanda_atual: Decimal
    mensagem_confirmacao: str
    qr_code_comanda_hash: Optional[str] = None
