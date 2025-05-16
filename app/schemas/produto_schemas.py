from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime

class ProdutoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco_unitario: Decimal
    disponivel: Optional[bool] = True
    imagem_url: Optional[str] = None
    categoria_id: Optional[int] = None

class ProdutoCreate(ProdutoBase):
    pass

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco_unitario: Optional[Decimal] = None
    disponivel: Optional[bool] = None
    imagem_url: Optional[str] = None
    categoria_id: Optional[int] = None

class ProdutoOut(ProdutoBase):
    id: int
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True
