# app/db/models/comanda.py
import enum
import uuid # Importar uuid para gerar hashes únicos
from sqlalchemy import Column, ForeignKey, Enum as SAEnum, Numeric, Text, Integer, DateTime, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from decimal import Decimal # Importar Decimal

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

    # Valor bruto dos itens (sem taxa, sem desconto)
    valor_total_itens = Column(Numeric(10, 2), default=0.00, nullable=False)

    # Percentual da taxa de serviço (padrão 10.00, pode ser alterado por comanda)
    percentual_taxa_servico = Column(Numeric(5, 2), default=Decimal("10.00"), nullable=False)
    # Valor calculado da taxa de serviço (baseado em valor_total_itens * percentual_taxa_servico / 100)
    valor_taxa_servico = Column(Numeric(10, 2), default=0.00, nullable=False)

    valor_desconto = Column(Numeric(10, 2), default=0.00, nullable=False)

    # Valor pago diretamente (dinheiro, cartão, etc.)
    valor_pago = Column(Numeric(10, 2), default=0.00, nullable=False)
    # Crédito do cliente aplicado *nesta* comanda
    valor_credito_usado = Column(Numeric(10, 2), default=0.00, nullable=False)
    # Valor registrado como fiado
    valor_fiado = Column(Numeric(10, 2), default=0.00, nullable=False)

    # Crédito gerado *nesta* comanda por pagamento excedente
    valor_credito_gerado = Column(Numeric(10, 2), default=0.00, nullable=False)

    motivo_cancelamento = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)
    qr_code_comanda_hash = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Renomeei valor_total_calculado para valor_total_itens para clareza
    # O valor final a pagar será calculado dinamicamente ou em um serviço:
    # (valor_total_itens + valor_taxa_servico - valor_desconto)

    mesa = relationship("Mesa", back_populates="comandas")
    cliente = relationship("Cliente", back_populates="comandas")
    itens_pedido = relationship("ItemPedido", back_populates="comanda", cascade="all, delete-orphan")
    pagamentos = relationship("Pagamento", back_populates="comanda", cascade="all, delete-orphan")
    fiados_registrados = relationship("Fiado", back_populates="comanda", cascade="all, delete-orphan")
    venda = relationship("Venda", back_populates="comanda")

    def __init__(self, **kwargs):
        # Definir valor padrão para percentual_taxa_servico se não for fornecido
        if 'percentual_taxa_servico' not in kwargs:
            kwargs['percentual_taxa_servico'] = Decimal("10.00")
        super().__init__(**kwargs)
        if not self.qr_code_comanda_hash:
            self.qr_code_comanda_hash = str(uuid.uuid4())

    # Propriedade para calcular o valor total a pagar (incluindo taxa e desconto)
    @property
    def valor_final_a_pagar(self) -> Decimal:
        total_itens = self.valor_total_itens or Decimal("0.00")
        taxa = self.valor_taxa_servico or Decimal("0.00")
        desconto = self.valor_desconto or Decimal("0.00")
        return max(Decimal("0.00"), total_itens + taxa - desconto)

    # Propriedade para calcular o valor já coberto (pago + crédito usado + fiado)
    @property
    def valor_coberto(self) -> Decimal:
        pago = self.valor_pago or Decimal("0.00")
        credito_usado = self.valor_credito_usado or Decimal("0.00")
        fiado = self.valor_fiado or Decimal("0.00")
        # Nota: O valor fiado também conta como "coberto" para fins de status,
        # mas a dívida real permanece.
        return pago + credito_usado + fiado

    # Propriedade para calcular o saldo devedor atual
    @property
    def saldo_devedor(self) -> Decimal:
        return max(Decimal("0.00"), self.valor_final_a_pagar - self.valor_coberto)


