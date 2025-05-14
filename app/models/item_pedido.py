# app/db/models/item_pedido.py
from sqlalchemy import Column, ForeignKey, Integer, String, Numeric
from sqlalchemy.orm import relationship
from app.db.base import Base


class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id = Column(Integer, primary_key=True, index=True)
    id_comanda = Column(ForeignKey("comandas.id"), nullable=False)  # Relacionamento com Comanda
    id_produto = Column(ForeignKey("produtos.id"), nullable=False)  # Relacionamento com Produto
    quantidade = Column(Integer, nullable=False, default=1)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    preco_total = Column(Numeric(10, 2), nullable=False)

    # Relacionamentos
    comanda = relationship("Comanda", back_populates="itens_pedido")
    produto = relationship("Produto", back_populates="itens_pedido")

    def calcular_preco_total(self):
        self.preco_total = self.quantidade * self.preco_unitario
        return self.preco_total
