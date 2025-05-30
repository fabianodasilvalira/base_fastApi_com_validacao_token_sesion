from pydantic import BaseModel, Field, validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


class ProdutoBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255, description="Nome do produto")
    descricao: Optional[str] = Field(None, max_length=1000, description="Descrição do produto")
    preco_unitario: Decimal = Field(..., gt=0, decimal_places=2, description="Preço unitário do produto")
    disponivel: Optional[bool] = Field(True, description="Se o produto está disponível")
    imagem_url: Optional[str] = Field(None, max_length=255, description="URL da imagem do produto")
    categoria_id: Optional[int] = Field(None, gt=0, description="ID da categoria do produto")

    @validator('preco_unitario')
    def validar_preco(cls, v):
        if v <= 0:
            raise ValueError('Preço deve ser maior que zero')
        return v


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=255)
    descricao: Optional[str] = Field(None, max_length=1000)
    preco_unitario: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    disponivel: Optional[bool] = None
    imagem_url: Optional[str] = Field(None, max_length=255)
    categoria_id: Optional[int] = Field(None, gt=0)

    @validator('preco_unitario')
    def validar_preco(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Preço deve ser maior que zero')
        return v


class ProdutoOut(ProdutoBase):
    id: int
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class CategoriaComProdutosOut(BaseModel):
    categoria: str
    produtos: List[ProdutoOut]

    class Config:
        from_attributes = True
