# app/models/venda_produto_item.py (ou onde você centraliza os modelos)
from sqlalchemy import Column, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship
from app.db.base import Base


class VendaProdutoItem(Base):
    __tablename__ = "venda_produto"

    id_venda = Column(Integer, ForeignKey("vendas.id"), primary_key=True)
    id_produto = Column(Integer, ForeignKey("produtos.id"), primary_key=True)

    quantidade_vendida = Column(Integer, nullable=False)  # ADICIONADO
    preco_unitario_na_venda = Column(Float, nullable=False)  # ADICIONADO

    venda = relationship("Venda", back_populates="itens_venda")  # ADICIONADO
    produto = relationship("Produto", back_populates="itens_venda")  # ADICIONADO
