from pydantic import BaseModel, field_validator, model_validator, Field, computed_field
from enum import Enum
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime

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

# Schema simplificado para criação de item (entrada do usuário)
class ItemPedidoCreate(BaseModel):
    id_produto: int
    quantidade: int
    observacoes: Optional[str] = None

    @field_validator('quantidade')
    def quantidade_deve_ser_positiva(cls, v):
        if v <= 0:
            raise ValueError('A quantidade deve ser maior que zero')
        return v

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id_produto": 5,
                "quantidade": 2,
                "observacoes": "Sem glúten"
            }
        }

# Schema para atualização de status do pedido
class StatusPedidoUpdate(BaseModel):
    status: StatusPedido

    class Config:
        from_attributes = True

# Schema para criação de um pedido
class PedidoCreate(BaseModel):
    id_comanda: int
    id_usuario_registrou: Optional[int] = None
    mesa_id: Optional[int] = None  # Adicionado campo mesa_id
    tipo_pedido: TipoPedido = TipoPedido.INTERNO_MESA
    status_geral_pedido: StatusPedido = StatusPedido.RECEBIDO
    observacoes_pedido: Optional[str] = None
    itens: List[ItemPedidoCreate]

    @field_validator('id_comanda')
    def id_comanda_deve_ser_positivo(cls, v):
        if v <= 0:
            raise ValueError('O ID da comanda deve ser maior que zero')
        return v

    @field_validator('itens')
    def itens_nao_vazios(cls, v):
        if not v or len(v) == 0:
            raise ValueError('O pedido deve ter pelo menos um item')
        return v

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id_comanda": 101,
                "id_usuario_registrou": 12,
                "tipo_pedido": "Interno (Mesa)",
                "status_geral_pedido": "Recebido",
                "observacoes_pedido": "Sem cebola",
                "itens": [
                    {
                        "id_produto": 5,
                        "quantidade": 2,
                        "observacoes": "Bem passada"
                    }
                ]
            }
        }

# Schema para dados da comanda no retorno do pedido
class ComandaEmPedido(BaseModel):
    id: int
    status_comanda: str
    qr_code_comanda_hash: str

    class Config:
        from_attributes = True

# Schema para dados do usuário no retorno do pedido
class UsuarioEmPedido(BaseModel):
    id: int
    nome: str
    email: str

    class Config:
        from_attributes = True

# Schema para dados da mesa no retorno do pedido
class MesaEmPedido(BaseModel):
    id: int
    numer_identificador: str
    stauts: str
    ar_code_hash: str

    class Config:
        from_attributes = True

# Schema de resposta do pedido
class Pedido(BaseModel):
    id: int
    comanda: Optional[ComandaEmPedido] = None
    usuario_registrou: Optional[UsuarioEmPedido] = None
    mesa: Optional[MesaEmPedido] = None
    tipo_pedido: TipoPedido
    status_geral_pedido: StatusPedido
    observacoes_pedido: Optional[str] = None
    motivo_cancelamento: Optional[str] = None
    itens: List["ItemPedido"]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# Schemas para interface pública (QRCode)
class PedidoPublicCreateSchema(BaseModel):
    itens: List["ItemPedidoPublicCreateSchema"]

class PedidoPublicResponseSchema(BaseModel):
    id_comanda: str
    status_comanda: str
    mesa_numero: Optional[str] = None
    itens_confirmados: List["ItemPedidoPublicResponseSchema"]
    valor_total_comanda_atual: Decimal
    mensagem_confirmacao: str
    qr_code_comanda_hash: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# Importações circulares resolvidas no final do arquivo
from app.schemas.item_pedido_schemas import (
    ItemPedido, 
    ItemPedidoPublicCreateSchema, ItemPedidoPublicResponseSchema
)
