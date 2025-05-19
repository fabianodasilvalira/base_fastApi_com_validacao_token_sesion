# app/schemas/mesa_schemas.py
from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime

# Definindo o StatusMesa como uma Enum do Pydantic
class StatusMesa(str, Enum):
    DISPONIVEL = "Disponível"
    OCUPADA = "Ocupada"
    RESERVADA = "Reservada"
    FECHADA = "Fechada"
    MANUTENCAO = "Manutenção"  # Adicionado para manter consistência com o modelo

# Schema para a criação de uma mesa
class MesaCreate(BaseModel):
    numero_identificador: str
    capacidade: Optional[int] = None
    status: StatusMesa = StatusMesa.DISPONIVEL
    qr_code_hash: Optional[str] = None
    id_cliente_associado: Optional[int] = None
    ativa_para_pedidos: bool = True

    class Config:
        from_attributes = True

# Schema para a resposta de uma mesa (ao buscar informações sobre a mesa)
class MesaOut(BaseModel):
    id: int
    numero_identificador: str
    capacidade: Optional[int] = None
    status: StatusMesa
    qr_code_hash: Optional[str] = None
    id_cliente_associado: Optional[int] = None
    ativa_para_pedidos: bool
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# Schema para a atualização de uma mesa
class MesaUpdate(BaseModel):
    numero_identificador: Optional[str] = None
    capacidade: Optional[int] = None
    status: Optional[StatusMesa] = None
    qr_code_hash: Optional[str] = None
    id_cliente_associado: Optional[int] = None
    ativa_para_pedidos: Optional[bool] = None

    class Config:
        from_attributes = True
