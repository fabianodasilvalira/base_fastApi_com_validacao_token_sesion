from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from enum import Enum
from typing import Optional
from decimal import Decimal


class StatusFiado(str, Enum):
    PENDENTE = "Pendente"
    PAGO_PARCIALMENTE = "Pago Parcialmente"
    PAGO_TOTALMENTE = "Pago Totalmente"
    CANCELADO = "Cancelado"


# Modelo base para todos os schemas de Fiado
class FiadoBase(BaseModel):
    id: int
    valor_original: Decimal
    valor_devido: Decimal
    data_registro: datetime
    data_vencimento: Optional[datetime] = None
    # Campos adicionais
    id_comanda: Optional[int] = None
    id_cliente: Optional[int] = None
    observacoes: Optional[str] = None

    class Config:
        from_attributes = True


# ✅ CORRIGIDO: Schema para criação de fiado compatível com o service
class FiadoCreate(BaseModel):
    """Schema para criação de um novo fiado"""
    id_comanda: Optional[int] = Field(None, description="ID da comanda associada ao fiado")
    id_cliente: Optional[int] = Field(None, description="ID do cliente associado ao fiado")
    id_usuario_registrou: Optional[int] = Field(None, description="ID do usuário que registrou o fiado")

    # ✅ CAMPO PRINCIPAL: valor_fiado (usado pelo service)
    valor_fiado: Decimal = Field(..., gt=0, description="Valor do fiado a ser registrado")

    # ✅ COMPATIBILIDADE: valor_original como alias
    valor_original: Optional[Decimal] = Field(None, gt=0, description="Valor original do fiado")
    valor_devido: Optional[Decimal] = Field(None, ge=0, description="Valor ainda devido do fiado")

    status_fiado: Optional[StatusFiado] = Field(StatusFiado.PENDENTE, description="Status atual do fiado")
    data_vencimento: Optional[date] = Field(None, description="Data de vencimento do fiado")
    observacoes: Optional[str] = Field(None, description="Observações sobre o fiado")

    class Config:
        from_attributes = True
        # ✅ PERMITE usar tanto valor_fiado quanto valor_original
        validate_by_name = True
        json_schema_extra = {
            "example": {
                "id_cliente": 123,
                "valor_fiado": 50.00,
                "observacoes": "Fiado autorizado pelo gerente",
                "data_vencimento": "2025-06-01"
            }
        }

    @validator('valor_devido')
    def valor_devido_nao_maior_que_original(cls, v, values):
        valor_original = values.get('valor_original') or values.get('valor_fiado')
        if valor_original and v and v > valor_original:
            raise ValueError('O valor devido não pode ser maior que o valor original')
        return v

    @validator('data_vencimento')
    def data_vencimento_futura(cls, v):
        if v and v < date.today():
            raise ValueError('A data de vencimento não pode ser no passado')
        return v

    # ✅ MÉTODO PARA COMPATIBILIDADE: retorna valor_fiado se valor_original não estiver definido
    def get_valor_original(self) -> Decimal:
        return self.valor_original or self.valor_fiado

    def get_valor_fiado(self) -> Decimal:
        return self.valor_fiado


# Schema para atualização de um fiado existente
class FiadoUpdate(BaseModel):
    id_comanda: Optional[int] = Field(None, gt=0, description="ID da comanda associada ao fiado")
    id_cliente: Optional[int] = Field(None, gt=0, description="ID do cliente associado ao fiado")
    id_usuario_registrou: Optional[int] = Field(None, description="ID do usuário que registrou o fiado")
    valor_original: Optional[Decimal] = Field(None, gt=0, description="Valor original do fiado")
    valor_devido: Optional[Decimal] = Field(None, ge=0, description="Valor ainda devido do fiado")
    status_fiado: Optional[StatusFiado] = Field(None, description="Status atual do fiado")
    data_vencimento: Optional[date] = Field(None, description="Data de vencimento do fiado")
    observacoes: Optional[str] = Field(None, description="Observações sobre o fiado")

    class Config:
        from_attributes = True

    @validator('valor_devido')
    def valor_devido_valido(cls, v, values):
        if v is not None and 'valor_original' in values and values['valor_original'] is not None and v > values[
            'valor_original']:
            raise ValueError('O valor devido não pode ser maior que o valor original')
        return v

    @validator('data_vencimento')
    def data_vencimento_futura(cls, v):
        if v and v < date.today():
            raise ValueError('A data de vencimento não pode ser no passado')
        return v


# Schema para resposta com dados completos do fiado
class FiadoSchema(BaseModel):
    """Schema completo para resposta de fiado"""
    id: int = Field(..., description="ID único do fiado")
    id_comanda: int = Field(..., gt=0, description="ID da comanda associada ao fiado")
    id_cliente: int = Field(..., gt=0, description="ID do cliente associado ao fiado")
    id_usuario_registrou: Optional[int] = Field(None, description="ID do usuário que registrou o fiado")
    valor_original: Decimal = Field(..., gt=0, description="Valor original do fiado")
    valor_devido: Decimal = Field(..., ge=0, description="Valor ainda devido do fiado")
    status_fiado: StatusFiado = Field(default=StatusFiado.PENDENTE, description="Status atual do fiado")
    data_registro: datetime = Field(..., description="Data de registro do fiado")
    data_vencimento: Optional[date] = Field(None, description="Data de vencimento do fiado")
    observacoes: Optional[str] = Field(None, description="Observações sobre o fiado")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "id_comanda": 123,
                "id_cliente": 456,
                "id_usuario_registrou": 789,
                "valor_original": 150.00,
                "valor_devido": 100.00,
                "status_fiado": "Pago Parcialmente",
                "data_registro": "2025-05-19T10:30:00",
                "data_vencimento": "2025-06-01",
                "observacoes": "Pagamento parcial realizado em 15/05/2025"
            }
        }


# Schema para representar um pagamento feito em um fiado
class FiadoPagamentoSchema(BaseModel):
    valor_pago: Decimal = Field(..., gt=0, description="Valor do pagamento realizado")
    id_usuario_registrou: Optional[int] = Field(None, description="ID do usuário que registrou o pagamento")
    observacoes: Optional[str] = Field(None, description="Observações sobre o pagamento")
    data_pagamento: date = Field(default_factory=date.today, description="Data do pagamento")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "valor_pago": 50.00,
                "id_usuario_registrou": 789,
                "observacoes": "Pagamento parcial",
                "data_pagamento": "2025-05-19"
            }
        }


# ✅ SCHEMA PARA RESPOSTA EM COMANDAS (usado nos relacionamentos)
class FiadoInResponse(BaseModel):
    """Schema para fiado em respostas de comanda"""
    id: int
    valor_original: Decimal
    valor_devido: Decimal
    data_registro: datetime
    data_vencimento: Optional[datetime] = None
    id_comanda: Optional[int] = None
    id_cliente: Optional[int] = None
    observacoes: Optional[str] = None

    class Config:
        from_attributes = True
