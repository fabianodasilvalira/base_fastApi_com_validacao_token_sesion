# app/db/models/pedido.py
import enum
from sqlalchemy import Column, ForeignKey, Enum as SAEnum, Integer, Numeric, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class StatusPedido(str, enum.Enum):
    RECEBIDO = "Recebido"
    EM_PREPARO = "Em Preparo"
    PRONTO_PARA_ENTREGA = "Pronto para Entrega"
    ENTREGUE_NA_MESA = "Entregue na Mesa"
    SAIU_PARA_ENTREGA_EXTERNA = "Saiu para Entrega (Externa)"
    ENTREGUE_CLIENTE_EXTERNO = "Entregue (Cliente Externo)"
    CANCELADO = "Cancelado"

class TipoPedido(str, enum.Enum):
    INTERNO_MESA = "Interno (Mesa)"
    EXTERNO_DELIVERY = "Externo (Delivery)"
    EXTERNO_RETIRADA = "Externo (Retirada)"

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_comanda = Column(ForeignKey("comandas.id"), nullable=False)
    id_usuario_registrou = Column(ForeignKey("users.id"), nullable=True)

    tipo_pedido = Column(SAEnum(TipoPedido), default=TipoPedido.INTERNO_MESA, nullable=False)
    status_geral_pedido = Column(SAEnum(StatusPedido), default=StatusPedido.RECEBIDO, nullable=False)
    observacoes_pedido = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    comanda = relationship("Comanda")
    usuario_registrou = relationship("User")
    itens = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")