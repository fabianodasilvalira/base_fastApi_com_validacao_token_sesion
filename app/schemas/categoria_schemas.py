from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class CategoriaBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    imagem_url: Optional[HttpUrl] = None

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaUpdate(CategoriaBase):
    pass

class CategoriaResponse(CategoriaBase):
    id: int
    criado_em: Optional[datetime]
    atualizado_em: Optional[datetime]

    class Config:
        from_attributes = True
