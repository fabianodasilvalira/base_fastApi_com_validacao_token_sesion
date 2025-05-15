from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class ProdutoCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco_unitario: Decimal
    categoria: Optional[str] = None
    disponivel: Optional[bool] = True

class ProdutoUpdate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco_unitario: Decimal
    categoria: Optional[str] = None
    disponivel: Optional[bool] = True

class ProdutoOut(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    preco_unitario: Decimal
    categoria: Optional[str] = None
    disponivel: Optional[bool] = True

    class Config:
        from_attributes = True
