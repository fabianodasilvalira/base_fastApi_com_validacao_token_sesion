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

class ComandaUpdate(BaseModel):
    id_mesa: Optional[str] = None
    id_cliente_associado: Optional[str] = None
    status_comanda: Optional[StatusComanda] = None
    valor_total_calculado: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    valor_pago: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    valor_fiado: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    observacoes: Optional[str] = None

class ComandaInResponse(BaseModel):
    id: str
    id_mesa: str
    id_cliente_associado: Optional[str] = None
    status_comanda: StatusComanda
    valor_total_calculado: condecimal(max_digits=10, decimal_places=2)
    valor_pago: condecimal(max_digits=10, decimal_places=2)
    valor_fiado: condecimal(max_digits=10, decimal_places=2)
    observacoes: Optional[str] = None

    class Config:
        orm_mode = True
