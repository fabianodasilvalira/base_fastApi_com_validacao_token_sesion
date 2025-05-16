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
    MANUTENCAO = "Manutenção"  # Adicionado para manter consistência com o modelo

# Schema para a criação de uma mesa
class MesaCreate(BaseModel):
    numero_identificador: str
    capacidade: Optional[int] = None
    status: StatusMesa = StatusMesa.DISPONIVEL
    qr_code_hash: Optional[str] = None
    id_cliente_associado: Optional[int] = None  # Corrigido para int para compatibilidade com o modelo
    ativa_para_pedidos: bool = True  # Adicionado campo que estava faltando

    class Config:
        from_attributes = True  # Permite que o Pydantic converta os dados da ORM para um formato Pydantic

# Schema para a resposta de uma mesa (ao buscar informações sobre a mesa)
class MesaOut(MesaCreate):
    id: int
    criado_em: Optional[str] = None
    atualizado_em: Optional[str] = None

# Schema para a atualização de uma mesa
class MesaUpdate(BaseModel):
    numero_identificador: Optional[str] = None
    capacidade: Optional[int] = None
    status: Optional[StatusMesa] = None
    qr_code_hash: Optional[str] = None
    id_cliente_associado: Optional[int] = None  # Corrigido para int
    ativa_para_pedidos: Optional[bool] = None  # Adicionado campo que estava faltando
