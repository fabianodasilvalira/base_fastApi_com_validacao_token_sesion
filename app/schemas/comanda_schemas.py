# app/schemas/comanda_schemas_sugestao.py
from pydantic import BaseModel, condecimal, validator
from typing import Optional, List
from enum import Enum
from datetime import datetime
from decimal import Decimal # Importar Decimal

# Importar schemas relacionados (ajuste os caminhos conforme necessário)
# from app.schemas.item_pedido_schemas import ItemPedidoInResponse
# from app.schemas.pagamento_schemas import PagamentoResponseSchema

# Placeholder para schemas importados para o exemplo funcionar
class ItemPedidoInResponse(BaseModel):
    id: int
    nome_item: str
    quantidade: int
    valor_unitario: Decimal
    valor_total: Decimal

class PagamentoResponseSchema(BaseModel):
    id: int
    valor_pago: Decimal
    metodo_pagamento: str
    data_pagamento: datetime

class FiadoBase(BaseModel):
    id: int
    valor_original: Decimal
    valor_devido: Decimal
    data_registro: datetime
    data_vencimento: Optional[datetime] = None

class StatusComanda(str, Enum):
    ABERTA = "Aberta"
    FECHADA = "Fechada"
    PAGA_PARCIALMENTE = "Paga Parcialmente"
    PAGA_TOTALMENTE = "Paga Totalmente"
    CANCELADA = "Cancelada"
    EM_FIADO = "Em Fiado"

class ComandaBaseComanda(BaseModel):
    id: int
    status_comanda: str
    qr_code_comanda_hash: str

class ComandaCreate(BaseModel):
    id_mesa: int
    id_cliente_associado: Optional[int] = None
    status_comanda: StatusComanda = StatusComanda.ABERTA
    # Mantém valor_total_calculado para a soma dos itens
    valor_total_calculado: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    percentual_taxa_servico: condecimal(max_digits=5, decimal_places=2) = Decimal("10.00")
    valor_taxa_servico: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    valor_desconto: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00") # Adicionado desconto
    # Adicionado valor_final_comanda
    valor_final_comanda: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    valor_pago: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    valor_fiado: condecimal(max_digits=10, decimal_places=2) = Decimal("0.00")
    observacoes: Optional[str] = None
    qr_code_comanda_hash: Optional[str] = None

    @validator("qr_code_comanda_hash", pre=True, always=True)
    def validar_qr_code(cls, v):
        if not v or v.strip().lower() == "string":
            return None
        return v

class ComandaUpdate(BaseModel):
    id_mesa: Optional[int] = None
    id_cliente_associado: Optional[int] = None
    status_comanda: Optional[StatusComanda] = None
    # Mantém valor_total_calculado opcional
    valor_total_calculado: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    percentual_taxa_servico: Optional[condecimal(max_digits=5, decimal_places=2)] = None
    valor_taxa_servico: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    valor_desconto: Optional[condecimal(max_digits=10, decimal_places=2)] = None # Adicionado desconto
    # Adicionado valor_final_comanda opcional
    valor_final_comanda: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    valor_pago: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    valor_fiado: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    observacoes: Optional[str] = None
    # qr_code_comanda_hash não deve ser atualizável geralmente

class ComandaInResponse(BaseModel):
    id: int
    id_mesa: int
    id_cliente_associado: Optional[int] = None
    status_comanda: StatusComanda
    # Mantém valor_total_calculado
    valor_total_calculado: condecimal(max_digits=10, decimal_places=2)
    percentual_taxa_servico: condecimal(max_digits=5, decimal_places=2)
    valor_taxa_servico: condecimal(max_digits=10, decimal_places=2)
    valor_desconto: condecimal(max_digits=10, decimal_places=2) # Adicionado desconto
    # Adicionado valor_final_comanda
    valor_final_comanda: condecimal(max_digits=10, decimal_places=2)
    valor_pago: condecimal(max_digits=10, decimal_places=2)
    valor_fiado: condecimal(max_digits=10, decimal_places=2)
    observacoes: Optional[str] = None
    qr_code_comanda_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # Campos opcionais para relacionamentos
    itens_pedido: Optional[List[ItemPedidoInResponse]] = None
    pagamentos: Optional[List[PagamentoResponseSchema]] = None
    fiados_registrados: Optional[List[FiadoBase]] = None

    class Config:
        from_attributes = True

class QRCodeHashResponse(BaseModel):
    qr_code_comanda_hash: str

