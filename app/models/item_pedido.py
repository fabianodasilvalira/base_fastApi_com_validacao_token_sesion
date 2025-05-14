from sqlalchemy import Column, ForeignKey, Integer, Numeric, DateTime, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.pedido import StatusPedido
from enum import Enum as PyEnum


# Definir o StatusPedido como Enum do SQLAlchemy
class StatusPedidoEnum(PyEnum):
    RECEBIDO = "Recebido"
    PREPARANDO = "Preparando"
    PRONTO = "Pronto"
    FINALIZADO = "Finalizado"
    CANCELADO = "Cancelado"


class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_pedido = Column(ForeignKey("pedidos.id"), nullable=False)
    id_comanda = Column(ForeignKey("comandas.id"), nullable=False)
    id_produto = Column(ForeignKey("produtos.id"), nullable=False)

    quantidade = Column(Integer, nullable=False, default=1)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    preco_total = Column(Numeric(10, 2), nullable=False)
    observacoes = Column(Text, nullable=True)

    # Usando Enum para status de pedido
    status = Column(Enum(StatusPedidoEnum), default=StatusPedidoEnum.RECEBIDO, nullable=False)

    created_at = Column(DateTime, default=func.now())

    pedido = relationship("Pedido", back_populates="itens")
    comanda = relationship("Comanda", back_populates="itens_pedido")
    produto = relationship("Produto", back_populates="itens_pedido")

    def calcular_preco_total(self):
        self.preco_total = self.quantidade * self.preco_unitario
        return self.preco_total
