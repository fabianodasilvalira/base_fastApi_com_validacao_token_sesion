# app/schemas/public_pedido_schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal

class ItemPedidoPublicCreateSchema(BaseModel):
    produto_id: int
    quantidade: int = Field(gt=0) # Quantidade deve ser maior que zero
    observacao: Optional[str] = None

class PedidoPublicCreateSchema(BaseModel):
    itens: List[ItemPedidoPublicCreateSchema]
    observacao_geral_pedido: Optional[str] = None

# Para a resposta, podemos reutilizar ou adaptar o ComandaInResponse ou criar um específico.
# Vamos supor uma resposta simplificada para o cliente, focando no essencial.

class ItemPedidoPublicResponseSchema(BaseModel):
    produto_nome: str # Nome do produto para clareza
    quantidade: int
    preco_unitario: Decimal
    preco_total_item: Decimal
    observacao: Optional[str] = None

class PedidoPublicResponseSchema(BaseModel):
    id_comanda: str # Ou int, dependendo do tipo do ID da comanda
    status_comanda: str
    mesa_numero: Optional[str] = None # Número da mesa para confirmação
    itens_confirmados: List[ItemPedidoPublicResponseSchema]
    valor_total_comanda_atual: Decimal
    mensagem_confirmacao: str
    qr_code_comanda_hash: Optional[str] = None # Para acompanhamento futuro da comanda específica


