from pydantic import BaseModel
from typing import Optional


class ClienteBase(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    observacoes: Optional[str] = None
    endereco: Optional[str] = None


class ClienteCreate(ClienteBase):
    nome: str
    telefone: str


class ClienteUpdate(ClienteBase):
    pass


class ClienteInDB(ClienteBase):
    id: str
    nome: str
    telefone: str
    observacoes: Optional[str] = None
    endereco: Optional[str] = None

    class Config:
        from_attributes = True


class ClienteOut(ClienteInDB):
    pass
