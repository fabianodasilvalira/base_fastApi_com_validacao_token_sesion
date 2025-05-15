from pydantic import BaseModel  # Adicionando BaseModel do Pydantic
from datetime import date
from enum import Enum

class StatusFiado(str, Enum):
    PENDENTE = "Pendente"
    PAGO_PARCIALMENTE = "Pago Parcialmente"
    PAGO_TOTALMENTE = "Pago Totalmente"
    CANCELADO = "Cancelado"

# FiadoBase agora é um modelo explícito sem herança
class FiadoBase(BaseModel):
    id_comanda: int
    id_cliente: int
    id_usuario_registrou: int | None = None
    valor_original: float
    valor_devido: float
    status_fiado: StatusFiado = StatusFiado.PENDENTE
    data_vencimento: date | None = None
    observacoes: str | None = None

    class Config:
        from_attributes = True  # Isso permite que Pydantic use objetos SQLAlchemy como entradas.

# FiadoCreate agora é definido explicitamente
class FiadoCreate(BaseModel):
    id_comanda: int
    id_cliente: int
    id_usuario_registrou: int | None = None
    valor_original: float
    valor_devido: float
    status_fiado: StatusFiado = StatusFiado.PENDENTE
    data_vencimento: date | None = None
    observacoes: str | None = None

    class Config:
        from_attributes = True

# FiadoUpdate agora é definido explicitamente
class FiadoUpdate(BaseModel):
    id_comanda: int
    id_cliente: int
    id_usuario_registrou: int | None = None
    valor_original: float
    valor_devido: float
    status_fiado: StatusFiado = StatusFiado.PENDENTE
    data_vencimento: date | None = None
    observacoes: str | None = None

    class Config:
        from_attributes = True

# Fiado agora é definido explicitamente
class Fiado(BaseModel):
    id: int
    id_comanda: int
    id_cliente: int
    id_usuario_registrou: int | None = None
    valor_original: float
    valor_devido: float
    status_fiado: StatusFiado = StatusFiado.PENDENTE
    data_vencimento: date | None = None
    observacoes: str | None = None

    class Config:
        from_attributes = True


# Schema para representar um pagamento feito em um fiado
class FiadoPagamentoSchema(BaseModel):
    id_fiado: int
    valor_pago: float
    data_pagamento: date
    observacao: str | None = None

    class Config:
        from_attributes = True
