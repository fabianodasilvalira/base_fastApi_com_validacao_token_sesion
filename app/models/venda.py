from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy.dialects.postgresql import UUID


class Venda(Base):
    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    valor_total = Column(Numeric(10, 2), nullable=False)  # Melhor para valores monetários
    data_venda = Column(Date, nullable=False)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)  # Se aplicável
    comanda_id = Column(Integer, ForeignKey("comandas.id"), nullable=True)  # Se aplicável

    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    # Relacionamentos
    usuario = relationship("User", back_populates="vendas")
    cliente = relationship("Cliente", back_populates="vendas")  # Se aplicável
    comanda = relationship("Comanda", back_populates="venda")  # Se aplicável
    pagamentos = relationship("Pagamento", back_populates="venda")  # Se aplicável
    itens_venda = relationship("VendaProdutoItem", back_populates="venda", cascade="all, delete-orphan")  # ADICIONADO
