from pydantic import BaseModel, condecimal
from typing import Optional
from enum import Enum

class StatusComanda(str, Enum):
    ABERTA = "Aberta"
    FECHADA = "Fechada"
    PAGA_PARCIALMENTE = "Paga Parcialmente"
    PAGA_TOTALMENTE = "Paga Totalmente"
    CANCELADA = "Cancelada"
    EM_FIADO = "Em Fiado"

class ComandaCreate(BaseModel):
    id_mesa: str
    id_cliente_associado: Optional[str] = None
    status_comanda: StatusComanda = StatusComanda.ABERTA
    valor_total_calculado: condecimal(max_digits=10, decimal_places=2) = 0.00
    valor_pago: condecimal(max_digits=10, decimal_places=2) = 0.00
    valor_fiado: condecimal(max_digits=10, decimal_places=2) = 0.00
    observacoes: Optional[str] = None
    qr_code_comanda_hash: Optional[str] = None # Adicionado para criação, se gerado no momento

class ComandaUpdate(BaseModel):
    id_mesa: Optional[str] = None
    id_cliente_associado: Optional[str] = None
    status_comanda: Optional[StatusComanda] = None
    valor_total_calculado: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    valor_pago: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    valor_fiado: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    observacoes: Optional[str] = None
    qr_code_comanda_hash: Optional[str] = None # Adicionado para atualização

class ComandaInResponse(BaseModel):
    id: str # Alterado para str para consistência, verificar se no model é int ou str
    id_mesa: str
    id_cliente_associado: Optional[str] = None
    status_comanda: StatusComanda
    valor_total_calculado: condecimal(max_digits=10, decimal_places=2)
    valor_pago: condecimal(max_digits=10, decimal_places=2)
    valor_fiado: condecimal(max_digits=10, decimal_places=2)
    observacoes: Optional[str] = None
    qr_code_comanda_hash: Optional[str] = None # Adicionado para resposta

    class Config:
        from_attributes = True

