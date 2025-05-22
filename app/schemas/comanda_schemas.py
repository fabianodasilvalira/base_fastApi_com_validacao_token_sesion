from pydantic import BaseModel, condecimal, validator
from typing import Optional, List
from enum import Enum
from datetime import datetime

class ComandaBaseComanda(BaseModel):
    id: int
    status_comanda: str
    qr_code_comanda_hash: str


class StatusComanda(str, Enum):
    ABERTA = "Aberta"
    FECHADA = "Fechada"
    PAGA_PARCIALMENTE = "Paga Parcialmente"
    PAGA_TOTALMENTE = "Paga Totalmente"
    CANCELADA = "Cancelada"
    EM_FIADO = "Em Fiado"

class ComandaCreate(BaseModel):
    id_mesa: int
    id_cliente_associado: Optional[int] = None
    status_comanda: StatusComanda = StatusComanda.ABERTA
    valor_total_calculado: condecimal(max_digits=10, decimal_places=2) = 0.00
    valor_pago: condecimal(max_digits=10, decimal_places=2) = 0.00
    valor_fiado: condecimal(max_digits=10, decimal_places=2) = 0.00
    observacoes: Optional[str] = None
    qr_code_comanda_hash: Optional[str] = None

    @validator("qr_code_comanda_hash", pre=True, always=True)
    def validar_qr_code(cls, v):
        if not v or v.strip().lower() == "string":
            return None
        return v

class ComandaUpdate(BaseModel):
    id_mesa: Optional[int] = None  # Corrigido para int para consistência com o modelo
    id_cliente_associado: Optional[int] = None  # Corrigido para int para consistência com o modelo
    status_comanda: Optional[StatusComanda] = None
    valor_total_calculado: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    valor_pago: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    valor_fiado: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    observacoes: Optional[str] = None
    # qr_code_comanda_hash: Optional[str] = None

# Schemas adicionais para relacionamentos
class ItemPedidoBase(BaseModel):
    id: int
    nome_item: str
    quantidade: int
    valor_unitario: condecimal(max_digits=10, decimal_places=2)
    valor_total: condecimal(max_digits=10, decimal_places=2)

class PagamentoBase(BaseModel):
    id: int
    valor_pago: condecimal(max_digits=10, decimal_places=2)
    metodo_pagamento: str
    data_pagamento: datetime

class FiadoBase(BaseModel):
    id: int
    valor_original: condecimal(max_digits=10, decimal_places=2)
    valor_devido: condecimal(max_digits=10, decimal_places=2)
    data_registro: datetime
    data_vencimento: Optional[datetime] = None

class ComandaInResponse(BaseModel):
    id: int
    id_mesa: int  # Corrigido para int para consistência com o modelo
    id_cliente_associado: Optional[int] = None  # Corrigido para int para consistência com o modelo
    status_comanda: StatusComanda
    valor_total_calculado: condecimal(max_digits=10, decimal_places=2)
    valor_pago: condecimal(max_digits=10, decimal_places=2)
    valor_fiado: condecimal(max_digits=10, decimal_places=2)
    observacoes: Optional[str] = None
    qr_code_comanda_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # Campos opcionais para relacionamentos quando carregados
    itens_pedido: Optional[List[ItemPedidoBase]] = None
    pagamentos: Optional[List[PagamentoBase]] = None
    fiados_registrados: Optional[List[FiadoBase]] = None

    class Config:
        from_attributes = True

class QRCodeHashResponse(BaseModel):
    qr_code_comanda_hash: str
