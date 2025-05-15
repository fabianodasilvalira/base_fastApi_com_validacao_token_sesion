from pydantic import BaseModel
from typing import Optional


class VendaProdutoItemBase(BaseModel):
    id_produto: int
    quantidade_vendida: int
    preco_unitario_na_venda: float


class VendaProdutoItemCreate(VendaProdutoItemBase):
    id_venda: int


class VendaProdutoItemUpdate(BaseModel):
    quantidade_vendida: Optional[int] = None
    preco_unitario_na_venda: Optional[float] = None


class VendaProdutoItemOut(VendaProdutoItemBase):
    id_venda: int

    class Config:
        orm_mode = True
