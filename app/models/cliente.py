from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from app.db.base import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(String, primary_key=True, index=True)
    nome = Column(String, nullable=True, index=True)
    telefone = Column(String, nullable=True, index=True, unique=True)
    observacoes = Column(Text, nullable=True)
    endereco = Column(String, nullable=True)

    # Usando string para evitar importação circular
    mesas_associadas = relationship("Mesa", back_populates="cliente_associado")
    comandas = relationship("Comanda", back_populates="cliente")
