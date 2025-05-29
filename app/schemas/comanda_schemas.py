from pydantic import BaseModel, condecimal, validator, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime
from decimal import Decimal


class StatusComanda(str, Enum):
    ABERTA = "Aberta"
    FECHADA = "Fechada"
    PAGA_PARCIALMENTE = "Paga Parcialmente"
    PAGA_TOTALMENTE = "Paga Totalmente"
    CANCELADA = "Cancelada"
    EM_FIADO = "Em Fiado"


# ✅ CORRIGIDO: Schemas para relacionamentos com todos os campos obrigatórios
class ItemPedidoInResponse(BaseModel):
    id: int
    nome_item: str
    quantidade: int
    valor_unitario: Decimal
    valor_total: Decimal
    # Campos adicionais que podem existir no modelo
    id_comanda: Optional[int] = None
    id_produto: Optional[int] = None
    observacoes: Optional[str] = None

    class Config:
        from_attributes = True


class PagamentoResponseSchema(BaseModel):
    id: int
    valor_pago: Decimal
    metodo_pagamento: str
    data_pagamento: datetime  # ✅ CORRIGIDO: Usar data_pagamento em vez de created_at
    # Campos adicionais
    id_comanda: Optional[int] = None
    id_cliente: Optional[int] = None
    observacoes: Optional[str] = None

    class Config:
        from_attributes = True


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


class MesaBase(BaseModel):
    id: int
    numero_identificador: str  # ✅ CORRIGIDO: Campo correto da mesa
    status: str  # ✅ ADICIONADO: Status da mesa
    # Campos opcionais
    capacidade: Optional[int] = None
    descricao: Optional[str] = None

    class Config:
        from_attributes = True


class ClienteBase(BaseModel):
    id: int
    nome: str
    imagem_url: Optional[str] = None  # ✅ ADICIONADO: URL da imagem
    saldo_credito: Optional[Decimal] = None  # ✅ ADICIONADO: Saldo de crédito
    telefone: Optional[str] = None


    class Config:
        from_attributes = True


class ComandaCreate(BaseModel):
    id_mesa: int = Field(..., description="ID da mesa (obrigatório)")
    id_cliente_associado: Optional[int] = Field(None, description="ID do cliente (opcional)")
    status_comanda: StatusComanda = Field(StatusComanda.ABERTA, description="Status inicial da comanda")

    # ✅ CORRIGIDO: Valores monetários com defaults seguros
    valor_total_calculado: Optional[condecimal(max_digits=10, decimal_places=2)] = Field(
        Decimal("0.00"), description="Saldo devedor restante"
    )
    percentual_taxa_servico: Optional[condecimal(max_digits=5, decimal_places=2)] = Field(
        Decimal("10.00"), description="Percentual da taxa de serviço"
    )
    valor_taxa_servico: Optional[condecimal(max_digits=10, decimal_places=2)] = Field(
        Decimal("0.00"), description="Valor calculado da taxa de serviço"
    )
    valor_desconto: Optional[condecimal(max_digits=10, decimal_places=2)] = Field(
        Decimal("0.00"), description="Valor do desconto aplicado"
    )
    valor_final_comanda: Optional[condecimal(max_digits=10, decimal_places=2)] = Field(
        Decimal("0.00"), description="Total dos itens (sem taxa, sem desconto)"
    )
    valor_pago: Optional[condecimal(max_digits=10, decimal_places=2)] = Field(
        Decimal("0.00"), description="Valor já pago"
    )
    valor_fiado: Optional[condecimal(max_digits=10, decimal_places=2)] = Field(
        Decimal("0.00"), description="Valor registrado como fiado"
    )
    valor_credito_usado: Optional[condecimal(max_digits=10, decimal_places=2)] = Field(
        Decimal("0.00"), description="Valor de crédito utilizado"
    )

    # Campos opcionais
    observacoes: Optional[str] = Field(None, description="Observações da comanda")
    qr_code_comanda_hash: Optional[str] = Field(None, description="Hash do QR Code")

    @validator("id_mesa")
    def validar_id_mesa(cls, v):
        if v <= 0:
            raise ValueError("ID da mesa deve ser maior que zero")
        return v

    @validator("id_cliente_associado")
    def validar_id_cliente(cls, v):
        if v is not None and v <= 0:
            raise ValueError("ID do cliente deve ser maior que zero")
        return v

    @validator("qr_code_comanda_hash", pre=True, always=True)
    def validar_qr_code(cls, v):
        if not v or v.strip().lower() == "string":
            return None
        return v

    @validator("percentual_taxa_servico")
    def validar_percentual_taxa(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Percentual da taxa de serviço deve estar entre 0 e 100")
        return v

    # ✅ NOVO: Validator para garantir que valores None sejam convertidos para Decimal
    @validator("valor_total_calculado", "valor_taxa_servico", "valor_desconto",
               "valor_final_comanda", "valor_pago", "valor_fiado", "valor_credito_usado", pre=True)
    def converter_none_para_decimal(cls, v):
        if v is None:
            return Decimal("0.00")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id_mesa": 1,
                "id_cliente_associado": 123,
                "observacoes": "Mesa para 4 pessoas",
                "percentual_taxa_servico": 10.00
            }
        }


class ComandaUpdate(BaseModel):
    id_mesa: Optional[int] = None
    id_cliente_associado: Optional[int] = None
    status_comanda: Optional[StatusComanda] = None
    valor_total_calculado: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    percentual_taxa_servico: Optional[condecimal(max_digits=5, decimal_places=2)] = None
    valor_taxa_servico: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    valor_desconto: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    valor_final_comanda: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    valor_pago: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    valor_fiado: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    valor_credito_usado: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    observacoes: Optional[str] = None

    @validator("percentual_taxa_servico")
    def validar_percentual_taxa(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Percentual da taxa de serviço deve estar entre 0 e 100")
        return v


class ComandaInResponse(BaseModel):
    id: int
    id_mesa: int
    id_cliente_associado: Optional[int] = None
    status_comanda: StatusComanda

    # ✅ CORRIGIDO: Valores monetários nunca None
    valor_total_calculado: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    percentual_taxa_servico: condecimal(max_digits=5, decimal_places=2) = Decimal("10.00")
    valor_taxa_servico: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    valor_desconto: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    valor_final_comanda: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    valor_pago: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    valor_fiado: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    valor_credito_usado: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")

    # Campos opcionais
    observacoes: Optional[str] = None
    qr_code_comanda_hash: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # ✅ CORRIGIDO: Relacionamentos opcionais mas com estrutura correta
    mesa: Optional[MesaBase] = None
    cliente: Optional[ClienteBase] = None
    itens_pedido: Optional[List[ItemPedidoInResponse]] = []
    pagamentos: Optional[List[PagamentoResponseSchema]] = []
    fiados_registrados: Optional[List[FiadoBase]] = []

    # ✅ NOVO: Validator para garantir que valores None sejam convertidos
    @validator("valor_total_calculado", "percentual_taxa_servico", "valor_taxa_servico",
               "valor_desconto", "valor_final_comanda", "valor_pago", "valor_fiado",
               "valor_credito_usado", pre=True)
    def converter_none_para_decimal(cls, v):
        if v is None:
            return Decimal("0.00")
        return v

    @validator("itens_pedido", "pagamentos", "fiados_registrados", pre=True)
    def converter_none_para_lista(cls, v):
        if v is None:
            return []
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "id_mesa": 5,
                "id_cliente_associado": 123,
                "status_comanda": "Aberta",
                "valor_total_calculado": 85.50,
                "percentual_taxa_servico": 10.00,
                "valor_taxa_servico": 8.55,
                "valor_desconto": 0.00,
                "valor_final_comanda": 85.50,
                "valor_pago": 0.00,
                "valor_fiado": 0.00,
                "valor_credito_usado": 0.00,
                "observacoes": "Mesa para 4 pessoas",
                "qr_code_comanda_hash": "abc123-def456",
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }


class QRCodeHashResponse(BaseModel):
    qr_code_comanda_hash: str

    class Config:
        json_schema_extra = {
            "example": {
                "qr_code_comanda_hash": "abc123-def456-ghi789"
            }
        }


class ComandaStatusUpdate(BaseModel):
    """Schema específico para atualização de status"""
    status_comanda: StatusComanda
    motivo_cancelamento: Optional[str] = None

    @validator("motivo_cancelamento")
    def validar_motivo_cancelamento(cls, v, values):
        if values.get("status_comanda") == StatusComanda.CANCELADA and not v:
            raise ValueError("Motivo do cancelamento é obrigatório quando status é 'Cancelada'")
        return v


class ComandaResumo(BaseModel):
    """Schema para resumo da comanda (listagens)"""
    id: int
    id_mesa: int
    status_comanda: StatusComanda
    valor_total_calculado: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    valor_pago: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    created_at: datetime

    @validator("valor_total_calculado", "valor_pago", pre=True)
    def converter_none_para_decimal(cls, v):
        if v is None:
            return Decimal("0.00")
        return v

    class Config:
        from_attributes = True


class ComandaCreateResponse(BaseModel):
    """Schema específico para resposta de criação de comanda com relacionamentos"""
    id: int
    id_mesa: int
    id_cliente_associado: Optional[int] = None
    status_comanda: StatusComanda

    # Valores monetários
    valor_total_calculado: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    percentual_taxa_servico: condecimal(max_digits=5, decimal_places=2) = Decimal("10.00")
    valor_taxa_servico: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    valor_desconto: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    valor_final_comanda: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    valor_pago: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    valor_fiado: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    valor_credito_usado: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")

    # Campos opcionais
    observacoes: Optional[str] = None
    qr_code_comanda_hash: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # ✅ RELACIONAMENTOS SEMPRE PRESENTES (não opcionais)
    mesa: MesaBase
    cliente: Optional[ClienteBase] = None
    itens_pedido: List[ItemPedidoInResponse] = []
    pagamentos: List[PagamentoResponseSchema] = []
    fiados_registrados: List[FiadoBase] = []

    @validator("valor_total_calculado", "percentual_taxa_servico", "valor_taxa_servico",
               "valor_desconto", "valor_final_comanda", "valor_pago", "valor_fiado",
               "valor_credito_usado", pre=True)
    def converter_none_para_decimal(cls, v):
        if v is None:
            return Decimal("0.00")
        return v

    @validator("itens_pedido", "pagamentos", "fiados_registrados", pre=True)
    def converter_none_para_lista(cls, v):
        if v is None:
            return []
        return v

    class Config:
        from_attributes = True
