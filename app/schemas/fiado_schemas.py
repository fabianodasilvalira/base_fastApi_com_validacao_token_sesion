from pydantic import BaseModel, Field, validator, root_validator
from datetime import date, datetime
from enum import Enum
from typing import Optional
from decimal import Decimal

# Re-declarando StatusFiado para garantir que o schema seja auto-contido
class StatusFiado(str, Enum):
    PENDENTE = "Pendente"
    PAGO_PARCIALMENTE = "Pago Parcialmente"
    PAGO_TOTALMENTE = "Pago Totalmente"
    CANCELADO = "Cancelado"

# --- Schemas de Entrada (Requisição) ---

class FiadoCreate(BaseModel):
    """Schema para criação de um novo fiado"""
    id_comanda: int = Field(..., description="ID da comanda associada ao fiado")
    id_cliente: int = Field(..., description="ID do cliente associado ao fiado")
    id_usuario_registrou: Optional[int] = Field(None, description="ID do usuário que registrou o fiado")

    valor_original: Decimal = Field(..., gt=0, description="Valor original total do fiado")
    valor_devido: Optional[Decimal] = Field(None, ge=0, description="Valor ainda devido do fiado")

    status_fiado: Optional[StatusFiado] = Field(StatusFiado.PENDENTE, description="Status inicial do fiado (Pendente por padrão)")
    data_vencimento: Optional[date] = Field(None, description="Data de vencimento do fiado")
    observacoes: Optional[str] = Field(None, max_length=500, description="Observações sobre o fiado")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id_comanda": 1,
                "id_cliente": 123,
                "valor_original": 50.00,
                "valor_devido": 50.00, # <-- ADICIONADO AQUI
                "observacoes": "Fiado autorizado pelo gerente",
                "data_vencimento": "2025-07-15"
            }
        }

    @root_validator(pre=True)
    def set_valor_devido_if_none(cls, values):
        """
        Define valor_devido como valor_original se não for fornecido na criação.
        """
        if 'valor_devido' not in values or values['valor_devido'] is None:
            if 'valor_original' in values and values['valor_original'] is not None:
                values['valor_devido'] = values['valor_original']
            # else: valor_original será validado por sua própria regra Field(..., gt=0)
        return values

    @validator('valor_devido')
    def valor_devido_nao_maior_que_original(cls, v, values):
        """
        Valida que o valor devido não seja maior que o valor original.
        """
        valor_original = values.get('valor_original')
        if valor_original is not None and v is not None and v > valor_original:
            raise ValueError('O valor devido não pode ser maior que o valor original.')
        return v

    @validator('data_vencimento')
    def data_vencimento_futura(cls, v):
        """
        Valida que a data de vencimento não seja no passado.
        """
        if v and v < date.today():
            raise ValueError('A data de vencimento não pode ser no passado.')
        return v


class FiadoUpdate(BaseModel):
    """Schema para atualização parcial de um fiado existente"""
    id_comanda: Optional[int] = Field(None, gt=0, description="ID da comanda associada ao fiado")
    id_cliente: Optional[int] = Field(None, gt=0, description="ID do cliente associado ao fiado")
    id_usuario_registrou: Optional[int] = Field(None, description="ID do usuário que registrou o fiado")
    valor_original: Optional[Decimal] = Field(None, gt=0, description="Novo valor original do fiado")
    valor_devido: Optional[Decimal] = Field(None, ge=0, description="Novo valor ainda devido do fiado")
    status_fiado: Optional[StatusFiado] = Field(None, description="Novo status do fiado")
    data_vencimento: Optional[date] = Field(None, description="Nova data de vencimento do fiado")
    observacoes: Optional[str] = Field(None, max_length=500, description="Novas observações sobre o fiado")

    class Config:
        from_attributes = True

    @validator('valor_devido')
    def valor_devido_valido(cls, v, values):
        # Esta validação só faz sentido se 'valor_original' também estiver sendo atualizado ou já existindo na instância
        # completa do Fiado (que não é o caso aqui, pois é um schema de UPDATE parcial)
        # O ideal é que essa validação seja feita no serviço, considerando o estado atual do fiado.
        # No entanto, se valor_original for fornecido junto com valor_devido, a validação ainda é útil.
        if v is not None and 'valor_original' in values and values['valor_original'] is not None and v > values['valor_original']:
            raise ValueError('O valor devido não pode ser maior que o valor original informado na atualização.')
        return v

    @validator('data_vencimento')
    def data_vencimento_futura(cls, v):
        if v and v < date.today():
            raise ValueError('A data de vencimento não pode ser no passado')
        return v


# --- Schemas de Saída (Resposta) ---

class FiadoSchema(BaseModel):
    """Schema completo para resposta de fiado"""
    id: int = Field(..., description="ID único do fiado")
    id_comanda: int = Field(..., gt=0, description="ID da comanda associada ao fiado")
    id_cliente: int = Field(..., gt=0, description="ID do cliente associado ao fiado")
    id_usuario_registrou: Optional[int] = Field(None, description="ID do usuário que registrou o fiado")
    valor_original: Decimal = Field(..., gt=0, description="Valor original do fiado")
    valor_devido: Decimal = Field(..., ge=0, description="Valor ainda devido do fiado")
    status_fiado: StatusFiado = Field(description="Status atual do fiado") # Não é Optional na resposta
    data_registro: datetime = Field(..., description="Data e hora de registro do fiado")
    data_vencimento: Optional[date] = Field(None, description="Data de vencimento do fiado")
    observacoes: Optional[str] = Field(None, description="Observações sobre o fiado")
    updated_at: datetime = Field(..., description="Data e hora da última atualização do fiado")


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
                "observacoes": "Pagamento parcial realizado em 15/05/2025",
                "updated_at": "2025-05-19T11:00:00"
            }
        }


class FiadoPagamentoSchema(BaseModel):
    """Schema para representar um pagamento feito em um fiado"""
    valor_pago: Decimal = Field(..., gt=0, description="Valor do pagamento realizado")
    id_usuario_registrou: Optional[int] = Field(None, description="ID do usuário que registrou o pagamento")
    observacoes: Optional[str] = Field(None, max_length=500, description="Observações sobre o pagamento")
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


# Schema para ser usado em respostas de relacionamentos (e.g., dentro de um schema de Comanda)
class FiadoInResponse(BaseModel):
    """Schema resumido para fiado em respostas de outras entidades (e.g., Comanda)"""
    id: int
    valor_original: Decimal
    valor_devido: Decimal
    status_fiado: StatusFiado
    data_registro: datetime
    data_vencimento: Optional[date] = None
    observacoes: Optional[str] = None
    # id_comanda e id_cliente são omitidos aqui, pois a comanda ou cliente já "contém" o fiado

    class Config:
        from_attributes = True