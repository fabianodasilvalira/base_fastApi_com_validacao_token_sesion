from pydantic import BaseModel, field_validator, model_validator, Field, computed_field
from enum import Enum
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

# Enum para o status do item de pedido
class StatusItemPedido(str, Enum):
    RECEBIDO = "Recebido"
    PREPARANDO = "Preparando"
    PRONTO = "Pronto"
    FINALIZADO = "Finalizado"
    CANCELADO = "Cancelado"

# Schema para criação de item (entrada do usuário)
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
        json_schema_extra = {
            "example": {
                "id_produto": 5,
                "quantidade": 2,
                "observacoes": "Sem glúten"
            }
        }

# Schema para atualização de item
class ItemPedidoUpdate(BaseModel):
    quantidade: Optional[int] = None
    observacoes: Optional[str] = None
    status: Optional[StatusItemPedido] = None  # Adicionado campo status

    class Config:
        from_attributes = True

# Schema de resposta do item
class ItemPedido(BaseModel):
    id: int
    id_pedido: int
    id_comanda: int  # Adicionado campo id_comanda
    id_produto: int
    quantidade: int
    preco_unitario: Decimal
    preco_total: Decimal  # Adicionado campo preco_total
    observacoes: Optional[str] = None
    status: StatusItemPedido  # Adicionado campo status
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None  # Adicionado campo updated_at

    @computed_field
    def preco_total_item(self) -> Decimal:
        return self.quantidade * self.preco_unitario

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# Schema para resposta de item de pedido (usado nas rotas)
class ItemPedidoInResponse(BaseModel):
    id: int
    id_pedido: int
    id_comanda: int  # Adicionado campo id_comanda
    id_produto: int
    quantidade: int
    preco_unitario: Decimal
    preco_total: Decimal  # Adicionado campo preco_total
    observacoes: Optional[str] = None
    status: StatusItemPedido  # Adicionado campo status
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None  # Adicionado campo updated_at

    @computed_field
    def preco_total_item(self) -> Decimal:
        return self.quantidade * self.preco_unitario

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# Schemas para interface pública
class ItemPedidoPublicCreateSchema(BaseModel):
    produto_id: int
    quantidade: int
    observacoes: Optional[str] = None

class ItemPedidoPublicResponseSchema(BaseModel):
    produto_nome: str
    quantidade: int
    preco_unitario: Decimal
    observacoes: Optional[str] = None
    status: Optional[str] = None  # Adicionado campo status

    @computed_field
    def preco_total_item(self) -> Decimal:
        return self.quantidade * self.preco_unitario