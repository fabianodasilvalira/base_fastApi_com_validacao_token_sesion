# app/db/models/fiado.py
import enum
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Enum as SAEnum, Numeric, Text, Date, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class StatusFiado(str, enum.Enum):
    PENDENTE = "Pendente"
    PAGO_PARCIALMENTE = "Pago Parcialmente"
    PAGO_TOTALMENTE = "Pago Totalmente"
    CANCELADO = "Cancelado"

class Fiado(Base):
    __tablename__ = "fiados"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_comanda = Column(ForeignKey("comandas.id"), nullable=False)
    id_cliente = Column(ForeignKey("clientes.id"), nullable=False)
    id_usuario_registrou = Column(ForeignKey("users.id"), nullable=True)

    valor_original = Column(Numeric(10, 2), nullable=False)
    valor_devido = Column(Numeric(10, 2), nullable=False)
    status_fiado = Column(SAEnum(StatusFiado), default=StatusFiado.PENDENTE, nullable=False)
    data_vencimento = Column(Date, nullable=True)
    observacoes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    comanda = relationship("Comanda", back_populates="fiados_registrados")
    cliente = relationship("Cliente", back_populates="fiados_registrados")
    usuario_registrou = relationship("User", foreign_keys=[id_usuario_registrou])