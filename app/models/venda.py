from sqlalchemy import Column, Integer, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy.dialects.postgresql import UUID

class Venda(Base):
    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True, index=True)
    valor_total = Column(Float, nullable=False)
    data_venda = Column(Date, nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relacionamento com o usuário
    usuario = relationship("User", back_populates="vendas")

    # Relacionamento com produtos (usando a tabela de junção)
    produtos = relationship("Produto", secondary="venda_produto", back_populates="vendas")