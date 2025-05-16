from pydantic import BaseModel
from typing import Optional


class ClienteBase(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    observacoes: Optional[str] = None
    endereco: Optional[str] = None
    imagem_url: Optional[str] = None  # Adicionado


class ClienteCreate(ClienteBase):
    nome: str
    telefone: str


class ClienteUpdate(ClienteBase):
    pass


class ClienteInDB(ClienteBase):
    id: int  # Alterado de str para int
    nome: str
    telefone: str
    observacoes: Optional[str] = None
    endereco: Optional[str] = None

    class Config:
        from_attributes = True


class ClienteOut(ClienteInDB):
    pass

