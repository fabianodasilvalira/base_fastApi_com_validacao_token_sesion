from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
import enum
from sqlalchemy import Enum as SAEnum
from app.db.base import Base

class StatusMesa(str, enum.Enum):
    DISPONIVEL = "Disponível"
    OCUPADA = "Ocupada"
    RESERVADA = "Reservada"
    FECHADA = "Fechada"

class Mesa(Base):
    __tablename__ = "mesas"

    id = Column(String, primary_key=True, index=True)
    numero_identificador = Column(String, nullable=False, unique=True, index=True)
    capacidade = Column(Integer, nullable=True)
    status = Column(SAEnum(StatusMesa), default=StatusMesa.DISPONIVEL, nullable=False)
    qr_code_hash = Column(String, nullable=True, unique=True, index=True)
    id_cliente_associado = Column(ForeignKey("clientes.id"), nullable=True)

    # Usando string para evitar importação circular
    cliente_associado = relationship("Cliente", back_populates="mesas_associadas")
    comandas = relationship("Comanda", back_populates="mesa")
    pedidos = relationship("Pedido", back_populates="mesa")  # Relacionamento reverso
