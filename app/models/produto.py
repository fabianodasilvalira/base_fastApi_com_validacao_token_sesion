from sqlalchemy import Column, String, Boolean, Numeric, Text, Integer, ForeignKey, DateTime, func, Sequence
from sqlalchemy.orm import relationship
from app.db.base import Base


class Produto(Base):
    __tablename__ = "produtos"

    # Definindo explicitamente a sequência
    id = Column(
        Integer,
        Sequence('produtos_id_seq', start=1, increment=1),
        primary_key=True,
        index=True,
        autoincrement=True
    )
    nome = Column(String, nullable=False, index=True)
    descricao = Column(Text, nullable=True)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    disponivel = Column(Boolean, default=True, nullable=False)
    imagem_url = Column(String(255), nullable=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True, index=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    # Relacionamentos
    categoria_relacionada = relationship("Categoria", back_populates="produtos", lazy="selectin")
    itens_venda = relationship("VendaProdutoItem", back_populates="produto")
    itens_pedido = relationship("ItemPedido", back_populates="produto", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Produto(id={self.id}, nome='{self.nome}', preco={self.preco_unitario})>"
