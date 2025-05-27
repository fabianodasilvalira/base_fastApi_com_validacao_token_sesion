# app/db/models/comanda.py
import enum
import uuid
from sqlalchemy import Column, ForeignKey, Enum as SAEnum, Numeric, Text, Integer, DateTime, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from decimal import Decimal


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

    # CORREÇÃO: valor_total_calculado agora é o valor final (itens + taxa - desconto)
    valor_total_calculado = Column(Numeric(10, 2), default=0.00, nullable=False)

    # Percentual da taxa de serviço (padrão 10.00, pode ser alterado por comanda)
    percentual_taxa_servico = Column(Numeric(5, 2), default=Decimal("10.00"), nullable=False)
    # Valor calculado da taxa de serviço (baseado em valor_final_comanda * percentual_taxa_servico / 100)
    valor_taxa_servico = Column(Numeric(10, 2), default=0.00, nullable=False)

    valor_desconto = Column(Numeric(10, 2), default=0.00, nullable=False)
    # CORREÇÃO: valor_final_comanda agora é apenas o total dos itens
    valor_final_comanda = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)

    # Valor pago diretamente (dinheiro, cartão, etc.)
    valor_pago = Column(Numeric(10, 2), default=0.00, nullable=False)
    # Valor registrado como fiado
    valor_fiado = Column(Numeric(10, 2), default=0.00, nullable=False)

    motivo_cancelamento = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)
    qr_code_comanda_hash = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    mesa = relationship("Mesa", back_populates="comandas")
    cliente = relationship("Cliente", back_populates="comandas")
    itens_pedido = relationship("ItemPedido", back_populates="comanda", cascade="all, delete-orphan")
    pagamentos = relationship("Pagamento", back_populates="comanda", cascade="all, delete-orphan")
    fiados_registrados = relationship("Fiado", back_populates="comanda", cascade="all, delete-orphan")
    venda = relationship("Venda", back_populates="comanda")

    def __init__(self, **kwargs):
        if 'valor_final_comanda' in kwargs:
            kwargs['valor_final_comanda'] = kwargs.pop('valor_final_comanda')

        if 'percentual_taxa_servico' not in kwargs:
            kwargs['percentual_taxa_servico'] = Decimal("10.00")

        super().__init__(**kwargs)

        # Atualiza os valores ao criar a comanda
        self.atualizar_valores_comanda()

        if not self.qr_code_comanda_hash:
            self.qr_code_comanda_hash = str(uuid.uuid4())

    def atualizar_valores_comanda(self):
        """
        CORREÇÃO: Atualiza os valores da comanda conforme nova lógica:
        - valor_final_comanda = apenas total dos itens
        - valor_total_calculado = total dos itens + taxa - desconto
        """
        # valor_final_comanda agora é apenas o total dos itens (sem taxa, sem desconto)
        total_itens = self.valor_final_comanda or Decimal("0.00")

        # Calcular taxa baseada no total dos itens
        percentual_taxa = self.percentual_taxa_servico or Decimal("0.00")
        self.valor_taxa_servico = (total_itens * percentual_taxa / Decimal("100")).quantize(Decimal("0.01"))

        # valor_total_calculado agora é o valor final a pagar (itens + taxa - desconto)
        taxa = self.valor_taxa_servico or Decimal("0.00")
        desconto = self.valor_desconto or Decimal("0.00")
        self.valor_total_calculado = max(Decimal("0.00"), total_itens + taxa - desconto)

    # Método público para atualizar valores
    def atualizar_valor_final_comanda(self):
        """Método público mantido para compatibilidade - chama o método principal"""
        self.atualizar_valores_comanda()

    # Método privado mantido para compatibilidade
    def _atualizar_valor_final(self):
        """Método privado mantido para compatibilidade - chama o método principal"""
        self.atualizar_valores_comanda()

    # Propriedade para calcular o valor total a pagar (incluindo taxa e desconto)
    @property
    def valor_final_a_pagar(self) -> Decimal:
        """Retorna o valor total a pagar (valor_total_calculado)"""
        return self.valor_total_calculado

    # Propriedade para calcular o valor já coberto (pago + fiado)
    @property
    def valor_coberto(self) -> Decimal:
        pago = self.valor_pago or Decimal("0.00")
        fiado = self.valor_fiado or Decimal("0.00")
        return pago + fiado

    # Propriedade para calcular o saldo devedor atual
    @property
    def saldo_devedor(self) -> Decimal:
        """Saldo devedor baseado no valor_total_calculado (valor final a pagar)"""
        return max(Decimal("0.00"), self.valor_total_calculado - self.valor_coberto)

    # Propriedade para obter apenas o total dos itens
    @property
    def total_itens(self) -> Decimal:
        """Retorna apenas o total dos itens (valor_final_comanda)"""
        return self.valor_final_comanda or Decimal("0.00")
