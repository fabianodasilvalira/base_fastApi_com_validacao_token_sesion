# app/db/models/comanda.py
import enum
import uuid # Importar uuid para gerar hashes únicos
from sqlalchemy import Column, ForeignKey, Enum as SAEnum, Numeric, Text, Integer, DateTime, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class StatusComanda(str, enum.Enum):
    ABERTA = "Aberta"
    FECHADA = "Fechada"
    PAGA_PARCIALMENTE = "Paga Parcialmente"
    PAGA_TOTALMENTE = "Paga Totalmente"
    CANCELADA = "Cancelada"
    EM_FIADO = "Em Fiado"

class Comanda(Base):
    __tablename__ = "comandas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_mesa = Column(ForeignKey("mesas.id"), nullable=False)
    id_cliente_associado = Column(ForeignKey("clientes.id"), nullable=True)
    status_comanda = Column(SAEnum(StatusComanda), default=StatusComanda.ABERTA, nullable=False)
    valor_total_calculado = Column(Numeric(10, 2), default=0.00, nullable=False)
    valor_pago = Column(Numeric(10, 2), default=0.00, nullable=False)
    valor_fiado = Column(Numeric(10, 2), default=0.00, nullable=False)
    valor_desconto = Column(Numeric(10, 2), default=0.00, nullable=False)
    motivo_cancelamento = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)
    qr_code_comanda_hash = Column(String, unique=True, index=True, nullable=True) # Novo campo para QRCode da comanda
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    mesa = relationship("Mesa", back_populates="comandas")
    cliente = relationship("Cliente", back_populates="comandas")
    itens_pedido = relationship("ItemPedido", back_populates="comanda", cascade="all, delete-orphan")
    pagamentos = relationship("Pagamento", back_populates="comanda", cascade="all, delete-orphan")
    fiados_registrados = relationship("Fiado", back_populates="comanda", cascade="all, delete-orphan")
    venda = relationship("Venda", back_populates="comanda")

    # Poderia ter um método para gerar o hash do QRCode ao criar a comanda
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     if not self.qr_code_comanda_hash:
    #         self.qr_code_comanda_hash = str(uuid.uuid4())

