# app/schemas/mesa.py
from pydantic import BaseModel
from typing import Optional
from enum import Enum

# Definindo o StatusMesa como uma Enum do Pydantic
class StatusMesa(str, Enum):
    DISPONIVEL = "Disponível"
    OCUPADA = "Ocupada"
    RESERVADA = "Reservada"
    FECHADA = "Fechada"

# Schema para a criação de uma mesa
class MesaCreate(BaseModel):
    numero_identificador: str
    capacidade: Optional[int] = None
    status: StatusMesa = StatusMesa.DISPONIVEL
    qr_code_hash: Optional[str] = None
    id_cliente_associado: Optional[str] = None  # Pode ser nulo, uma mesa pode não ter cliente associado

    class Config:
        orm_mode = True  # Permite que o Pydantic converta os dados da ORM para um formato Pydantic

# Schema para a resposta de uma mesa (ao buscar informações sobre a mesa)
class MesaOut(MesaCreate):
    id: int

# Schema para a atualização de uma mesa
class MesaUpdate(BaseModel):
    numero_identificador: Optional[str] = None
    capacidade: Optional[int] = None
    status: Optional[StatusMesa] = None
    qr_code_hash: Optional[str] = None
    id_cliente_associado: Optional[str] = None
