from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class VendaProduto(Base):
    __tablename__ = "venda_produto"

    id_venda = Column(Integer, ForeignKey("vendas.id"), primary_key=True)
    id_produto = Column(Integer, ForeignKey("produtos.id"), primary_key=True)