from pydantic import BaseModel
from enum import Enum
from typing import Optional
from decimal import Decimal
from datetime import datetime


class MetodoPagamento(str, Enum):
    DINHEIRO = "Dinheiro"
    CARTAO_CREDITO = "Cartão de Crédito"
    CARTAO_DEBITO = "Cartão de Débito"
    PIX = "Pix"
    FIADO = "Fiado"
    OUTRO = "Outro"


class StatusPagamento(str, Enum):
    PENDENTE = "Pendente"
    APROVADO = "Aprovado"
    REJEITADO = "Rejeitado"
    CANCELADO = "Cancelado"


class PagamentoCreateSchema(BaseModel):
    id_comanda: int
    id_cliente: Optional[int] = None
    id_usuario_registrou: Optional[int] = None
    id_venda: Optional[int] = None
    id_pedido: Optional[int] = None
    valor_pago: Decimal
    metodo_pagamento: MetodoPagamento
    status_pagamento: StatusPagamento = StatusPagamento.APROVADO
    detalhes_transacao: Optional[str] = None
    observacoes: Optional[str] = None


class PagamentoUpdateSchema(BaseModel):
    id_comanda: Optional[int] = None
    id_cliente: Optional[int] = None
    id_usuario_registrou: Optional[int] = None
    id_venda: Optional[int] = None
    id_pedido: Optional[int] = None
    valor_pago: Optional[Decimal] = None
    metodo_pagamento: Optional[MetodoPagamento] = None
    status_pagamento: Optional[StatusPagamento] = None
    detalhes_transacao: Optional[str] = None
    observacoes: Optional[str] = None


class PagamentoResponseSchema(BaseModel):
    id: int
    id_comanda: int
    id_cliente: Optional[int] = None
    id_usuario_registrou: Optional[int] = None
    id_venda: Optional[int] = None
    id_pedido: Optional[int] = None
    valor_pago: Decimal
    metodo_pagamento: MetodoPagamento
    status_pagamento: StatusPagamento
    detalhes_transacao: Optional[str] = None
    observacoes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
