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

    valor_total_calculado = Column(Numeric(10, 2), default=0.00, nullable=False)
    percentual_taxa_servico = Column(Numeric(5, 2), default=Decimal("10.00"), nullable=False)
    valor_taxa_servico = Column(Numeric(10, 2), default=0.00, nullable=False)
    valor_desconto = Column(Numeric(10, 2), default=0.00, nullable=False)
    valor_final_comanda = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    valor_pago = Column(Numeric(10, 2), default=0.00, nullable=False)
    valor_fiado = Column(Numeric(10, 2), default=0.00, nullable=False)  # ✅ SÓ CONTROLE
    valor_credito_usado = Column(Numeric(10, 2), default=0.00, nullable=False)
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
        self.atualizar_valores_comanda()

        if not self.qr_code_comanda_hash:
            self.qr_code_comanda_hash = str(uuid.uuid4())

    def recalcular_estrutura_comanda(self):
        """
        ✅ USAR APENAS quando alterar itens, taxa ou desconto
        Recalcula: valor_final_comanda, valor_taxa_servico
        """
        # Calcular total dos itens
        total_itens = self.valor_final_comanda or Decimal("0.00")

        # Calcular taxa baseada no total dos itens
        percentual_taxa = self.percentual_taxa_servico or Decimal("0.00")
        self.valor_taxa_servico = (total_itens * percentual_taxa / Decimal("100")).quantize(Decimal("0.01"))

    def recalcular_saldo_devedor(self):
        """
        ✅ CORREÇÃO PRINCIPAL: Só subtrai valor_pago + valor_credito
        valor_fiado é SÓ para controle, NÃO subtrai!
        """
        # Usar valores já calculados (NÃO recalcular estrutura!)
        total_itens = self.valor_final_comanda or Decimal("0.00")
        taxa = self.valor_taxa_servico or Decimal("0.00")
        desconto = self.valor_desconto or Decimal("0.00")
        valor_total_original = max(Decimal("0.00"), total_itens + taxa - desconto)

        # ✅ CORREÇÃO: NÃO subtrair valor_fiado (já está no valor_pago)
        valor_pago = self.valor_pago or Decimal("0.00")  # Inclui fiados
        valor_credito = self.valor_credito_usado or Decimal("0.00")

        # SÓ subtrai pago + crédito (fiado já está no pago)
        self.valor_total_calculado = max(Decimal("0.00"), valor_total_original - valor_pago - valor_credito)

    def atualizar_valores_comanda(self):
        """
        ✅ MÉTODO COMPLETO: Recalcula estrutura E saldo
        Usar apenas quando necessário recalcular tudo (itens/taxa/desconto alterados)
        """
        self.recalcular_estrutura_comanda()
        self.recalcular_saldo_devedor()

    @property
    def valor_total_original(self) -> Decimal:
        """Retorna o valor total original (itens + taxa - desconto) antes dos pagamentos"""
        total_itens = self.valor_final_comanda or Decimal("0.00")
        taxa = self.valor_taxa_servico or Decimal("0.00")
        desconto = self.valor_desconto or Decimal("0.00")
        return max(Decimal("0.00"), total_itens + taxa - desconto)

    @property
    def valor_coberto(self) -> Decimal:
        """
        ✅ CORREÇÃO: Retorna valor efetivamente coberto
        valor_pago já inclui fiados, então não somar valor_fiado novamente
        """
        pago = self.valor_pago or Decimal("0.00")  # Já inclui fiados
        credito = self.valor_credito_usado or Decimal("0.00")
        return pago + credito

    @property
    def valor_total_fiado_controle(self) -> Decimal:
        """Retorna o total de fiados APENAS para controle/relatórios"""
        return self.valor_fiado or Decimal("0.00")

    @property
    def saldo_devedor(self) -> Decimal:
        """Saldo devedor restante (valor_total_calculado)"""
        return self.valor_total_calculado

    @property
    def total_itens(self) -> Decimal:
        """Retorna apenas o total dos itens (valor_final_comanda)"""
        return self.valor_final_comanda or Decimal("0.00")

    @property
    def esta_ativa(self) -> bool:
        """Verifica se a comanda está ativa (aberta ou parcialmente paga)"""
        return self.status_comanda in [StatusComanda.ABERTA, StatusComanda.PAGA_PARCIALMENTE]
