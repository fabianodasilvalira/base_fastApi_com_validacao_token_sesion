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

    def atualizar_valores_comanda(self, apenas_saldo=False):
        """
        ✅ MÉTODO UNIFICADO CORRIGIDO: Atualiza valores da comanda de forma segura

        Args:
            apenas_saldo (bool): Se True, atualiza apenas o saldo devedor sem recalcular a estrutura
                                (usar após pagamentos). Se False, recalcula estrutura e saldo
                                (usar após alterações em itens, taxa ou desconto).
        """
        # Preservar valores originais para debug
        valor_total_antes = self.valor_total_calculado

        # PARTE 1: Recalcular estrutura (apenas se não for só atualização de saldo)
        if not apenas_saldo:
            # Calcular taxa baseada no total dos itens
            total_itens = self.valor_final_comanda or Decimal("0.00")
            percentual_taxa = self.percentual_taxa_servico or Decimal("0.00")
            self.valor_taxa_servico = (total_itens * percentual_taxa / Decimal("100")).quantize(Decimal("0.01"))

        # PARTE 2: Sempre recalcular o saldo devedor corretamente
        # Usar valores já calculados para o total original
        total_itens = self.valor_final_comanda or Decimal("0.00")
        taxa = self.valor_taxa_servico or Decimal("0.00")
        desconto = self.valor_desconto or Decimal("0.00")
        valor_total_original = max(Decimal("0.00"), total_itens + taxa - desconto)

        # Calcular valor coberto (pago + crédito)
        valor_pago = self.valor_pago or Decimal("0.00")  # Já inclui fiados
        valor_credito = self.valor_credito_usado or Decimal("0.00")

        # Calcular saldo devedor final
        self.valor_total_calculado = max(Decimal("0.00"), valor_total_original - valor_pago - valor_credito)

        # Log para debug (remover em produção)
        # print(f"Atualização: apenas_saldo={apenas_saldo}, antes={valor_total_antes}, depois={self.valor_total_calculado}")

    # Métodos legados mantidos para compatibilidade, mas redirecionando para o método unificado
    def recalcular_estrutura_comanda(self):
        """
        ✅ LEGADO: Usar atualizar_valores_comanda(apenas_saldo=False) em vez disso
        """
        self.atualizar_valores_comanda(apenas_saldo=False)

    def recalcular_saldo_devedor(self):
        """
        ✅ LEGADO: Usar atualizar_valores_comanda(apenas_saldo=True) em vez disso
        """
        self.atualizar_valores_comanda(apenas_saldo=True)

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
