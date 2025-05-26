# app/db/models/cliente.py
from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Numeric

from app.db.base import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String, nullable=False, index=True)
    telefone = Column(String, nullable=False, index=True)
    observacoes = Column(Text, nullable=True)
    endereco = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    imagem_url = Column(String(255), nullable=True, index=True)
    # saldo_credito = Column(Numeric(10, 2), default=0.00, nullable=False)

    mesas_associadas = relationship("Mesa", back_populates="cliente_associado")
    fiados_registrados = relationship("Fiado", back_populates="cliente")
    comandas = relationship("Comanda", back_populates="cliente")
    vendas = relationship("Venda", back_populates="cliente")