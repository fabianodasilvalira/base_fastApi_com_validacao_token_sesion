# app/schemas/fiado_schemas.py
from pydantic import BaseModel, Field, validator
from datetime import date
from enum import Enum
from typing import Optional

class StatusFiado(str, Enum):
    PENDENTE = "Pendente"
    PAGO_PARCIALMENTE = "Pago Parcialmente"
    PAGO_TOTALMENTE = "Pago Totalmente"
    CANCELADO = "Cancelado"

# Modelo base para todos os schemas de Fiado
class FiadoBase(BaseModel):
    id_comanda: int = Field(..., gt=0, description="ID da comanda associada ao fiado")
    id_cliente: int = Field(..., gt=0, description="ID do cliente associado ao fiado")
    id_usuario_registrou: Optional[int] = Field(None, description="ID do usuário que registrou o fiado")
    valor_original: float = Field(..., gt=0, description="Valor original do fiado")
    valor_devido: float = Field(..., ge=0, description="Valor ainda devido do fiado")
    status_fiado: StatusFiado = Field(default=StatusFiado.PENDENTE, description="Status atual do fiado")
    data_vencimento: Optional[date] = Field(None, description="Data de vencimento do fiado")
    observacoes: Optional[str] = Field(None, description="Observações sobre o fiado")

    class Config:
        from_attributes = True  # Permite que Pydantic use objetos SQLAlchemy como entradas

    @validator('valor_devido')
    def valor_devido_nao_maior_que_original(cls, v, values):
        if 'valor_original' in values and v > values['valor_original']:
            raise ValueError('O valor devido não pode ser maior que o valor original')
        return v

    @validator('data_vencimento')
    def data_vencimento_futura(cls, v):
        if v and v < date.today():
            raise ValueError('A data de vencimento não pode ser no passado')
        return v

# Schema para criação de um novo fiado
class FiadoCreate(FiadoBase):
    pass

# Schema para atualização de um fiado existente
class FiadoUpdate(BaseModel):
    id_comanda: Optional[int] = Field(None, gt=0, description="ID da comanda associada ao fiado")
    id_cliente: Optional[int] = Field(None, gt=0, description="ID do cliente associado ao fiado")
    id_usuario_registrou: Optional[int] = Field(None, description="ID do usuário que registrou o fiado")
    valor_original: Optional[float] = Field(None, gt=0, description="Valor original do fiado")
    valor_devido: Optional[float] = Field(None, ge=0, description="Valor ainda devido do fiado")
    status_fiado: Optional[StatusFiado] = Field(None, description="Status atual do fiado")
    data_vencimento: Optional[date] = Field(None, description="Data de vencimento do fiado")
    observacoes: Optional[str] = Field(None, description="Observações sobre o fiado")

    class Config:
        from_attributes = True

    @validator('valor_devido')
    def valor_devido_valido(cls, v, values):
        if v is not None and 'valor_original' in values and values['valor_original'] is not None and v > values['valor_original']:
            raise ValueError('O valor devido não pode ser maior que o valor original')
        return v

    @validator('data_vencimento')
    def data_vencimento_futura(cls, v):
        if v and v < date.today():
            raise ValueError('A data de vencimento não pode ser no passado')
        return v

# Schema para resposta com dados completos do fiado
class FiadoSchema(FiadoBase):
    id: int = Field(..., description="ID único do fiado")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "id_comanda": 123,
                "id_cliente": 456,
                "id_usuario_registrou": 789,
                "valor_original": 150.00,
                "valor_devido": 100.00,
                "status_fiado": "Pago Parcialmente",
                "data_vencimento": "2025-06-01",
                "observacoes": "Pagamento parcial realizado em 15/05/2025"
            }
        }

# Schema para representar um pagamento feito em um fiado
class FiadoPagamentoSchema(BaseModel):
    valor_pago: float = Field(..., gt=0, description="Valor do pagamento realizado")
    id_usuario_registrou: Optional[int] = Field(None, description="ID do usuário que registrou o pagamento")
    observacoes: Optional[str] = Field(None, description="Observações sobre o pagamento")
    data_pagamento: date = Field(default_factory=date.today, description="Data do pagamento")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "valor_pago": 50.00,
                "id_usuario_registrou": 789,
                "observacoes": "Pagamento parcial",
                "data_pagamento": "2025-05-19"
            }
        }
