from pydantic import BaseModel
from datetime import date
from typing import List

class ProdutoVendaSchemas(BaseModel):
    id: int
    nome: str
    preco_unitario: float
    quantidade_vendida: int
    preco_total: float

class VendaSchemas(BaseModel):
    id: int
    valor_total: float
    data_venda: date
    usuario_id: int
    produtos: List[ProdutoVendaSchemas]

    class Config:
        orm_mode = True
