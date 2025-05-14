from sqlalchemy import Column, String, Boolean, Numeric, Text, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, index=True)
    descricao = Column(Text, nullable=True)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    categoria = Column(String, nullable=True, index=True)
    disponivel = Column(Boolean, default=True)
    imagem_url = Column(String(255), nullable=True, index=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    categoria_relacionada = relationship("Categoria", back_populates="produtos")

    # Relacionamento com vendas através da tabela de junção
    vendas = relationship("Venda", secondary="venda_produto", back_populates="produtos")

    # Relacionamento com itens de pedido
    itens_pedido = relationship("ItemPedido", back_populates="produto", cascade="all, delete-orphan")