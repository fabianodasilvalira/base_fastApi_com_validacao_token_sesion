from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy.dialects.postgresql import UUID


class Venda(Base):
    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True, index=True)
    valor_total = Column(Numeric(10, 2), nullable=False)  # Melhor para valores monetários
    data_venda = Column(Date, nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)  # Se aplicável
    comanda_id = Column(Integer, ForeignKey("comandas.id"), nullable=True)  # Se aplicável

    # Relacionamentos
    usuario = relationship("User", back_populates="vendas")
    cliente = relationship("Cliente", back_populates="vendas")  # Se aplicável
    comanda = relationship("Comanda", back_populates="venda")  # Se aplicável
    pagamentos = relationship("Pagamento", back_populates="venda")  # Se aplicável

    # Relacionamento muitos-para-muitos com produtos
    produtos = relationship(
        "Produto",
        secondary="venda_produto",
        back_populates="vendas"
    )