# app/db/models/pagamento.py
import enum
from sqlalchemy import Column, ForeignKey, Enum as SAEnum, Numeric, String, Text, Integer, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class MetodoPagamento(str, enum.Enum):
    DINHEIRO = "Dinheiro"
    CARTAO_CREDITO = "Cartão de Crédito"
    CARTAO_DEBITO = "Cartão de Débito"
    PIX = "Pix"
    FIADO = "Fiado"
    OUTRO = "Outro"

class StatusPagamento(str, enum.Enum):
    PENDENTE = "Pendente"
    APROVADO = "Aprovado"
    REJEITADO = "Rejeitado"
    CANCELADO = "Cancelado"

class Pagamento(Base):
    __tablename__ = "pagamentos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_comanda = Column(ForeignKey("comandas.id"), nullable=False)
    id_cliente = Column(ForeignKey("clientes.id"), nullable=True)
    id_usuario_registrou = Column(ForeignKey("users.id"), nullable=True)
    id_venda = Column(ForeignKey("vendas.id"), nullable=True)
    id_pedido = Column(ForeignKey("pedidos.id"), nullable=True)

    valor_pago = Column(Numeric(10, 2), nullable=False)
    metodo_pagamento = Column(SAEnum(MetodoPagamento), nullable=False)
    status_pagamento = Column(SAEnum(StatusPagamento), default=StatusPagamento.APROVADO, nullable=False)
    detalhes_transacao = Column(String, nullable=True)
    observacoes = Column(Text, nullable=True)
    data_pagamento = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    comanda = relationship("Comanda", back_populates="pagamentos")
    cliente = relationship("Cliente")
    usuario_registrou = relationship("User", foreign_keys=[id_usuario_registrou])
    pedido = relationship("Pedido", back_populates="pagamentos")
    venda = relationship("Venda", back_populates="pagamentos")  # Relacionamento com Venda

