# app/db/models/comanda.py
import enum
from sqlalchemy import Column, ForeignKey, Enum as SAEnum, Numeric, Text, Integer
from sqlalchemy.orm import relationship
from app.db.base import Base

class StatusComanda(str, enum.Enum):
    ABERTA = "Aberta"
    FECHADA = "Fechada"
    PAGA_PARCIALMENTE = "Paga Parcialmente"
    PAGA_TOTALMENTE = "Paga Totalmente"
    CANCELADA = "Cancelada"
    EM_FIADO = "Em Fiado"

class Comanda(Base):
    __tablename__ = "comandas"

    id = Column(Integer, primary_key=True, index=True)
    id_mesa = Column(ForeignKey("mesas.id"), nullable=False)
    id_cliente_associado = Column(ForeignKey("clientes.id"), nullable=True)
    status_comanda = Column(SAEnum(StatusComanda), default=StatusComanda.ABERTA, nullable=False)
    valor_total_calculado = Column(Numeric(10, 2), default=0.00, nullable=False)
    valor_pago = Column(Numeric(10, 2), default=0.00, nullable=False)
    valor_fiado = Column(Numeric(10, 2), default=0.00, nullable=False)
    observacoes = Column(Text, nullable=True)

    # Use strings para evitar importação circular
    mesa = relationship("Mesa", back_populates="comandas")
    cliente = relationship("Cliente", back_populates="comandas")
    itens_pedido = relationship("ItemPedido", back_populates="comanda", cascade="all, delete-orphan")
    #pagamentos = relationship("Pagamento", back_populates="comanda", cascade="all, delete-orphan")
    #fiados_registrados = relationship("Fiado", back_populates="comanda", cascade="all, delete-orphan")