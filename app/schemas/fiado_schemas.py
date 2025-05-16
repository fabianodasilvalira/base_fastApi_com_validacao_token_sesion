from pydantic import BaseModel
from datetime import date
from enum import Enum

class StatusFiado(str, Enum):
    PENDENTE = "Pendente"
    PAGO_PARCIALMENTE = "Pago Parcialmente"
    PAGO_TOTALMENTE = "Pago Totalmente"
    CANCELADO = "Cancelado"

# Modelo base para todos os schemas de Fiado
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
        from_attributes = True  # Permite que Pydantic use objetos SQLAlchemy como entradas

# Schema para criação de um novo fiado
class FiadoCreate(FiadoBase):
    pass

# Schema para atualização de um fiado existente
class FiadoUpdate(FiadoBase):
    pass

# Schema para resposta com dados completos do fiado
class Fiado(FiadoBase):
    id: int

    class Config:
        from_attributes = True

# Schema para representar um pagamento feito em um fiado
class FiadoPagamentoSchema(BaseModel):
    valor_pago: float
    id_usuario_registrou: int | None = None
    observacoes: str | None = None
    data_pagamento: date = date.today()

    class Config:
        from_attributes = True
