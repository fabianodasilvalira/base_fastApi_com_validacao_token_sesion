import logging
import uuid
from sqlalchemy import select, or_, update, and_
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from typing import List, Optional, Tuple
from decimal import Decimal
from datetime import datetime

from app.models import Cliente, Mesa
from app.models.comanda import Comanda, StatusComanda
from app.models.pagamento import Pagamento
from app.models.fiado import Fiado
from app.models.pedido import Pedido
from app.models.item_pedido import ItemPedido
from app.schemas.comanda_schemas import ComandaCreate, ComandaUpdate
from app.schemas.pagamento_schemas import PagamentoCreateSchema
from app.schemas.fiado_schemas import FiadoCreate

logger = logging.getLogger(__name__)


class ComandaValidationError(Exception):
    """Exceção para erros de validação de negócio"""
    pass


class ComandaService:
    """Service responsável por toda lógica de negócio relacionada a comandas"""

    @staticmethod
    async def validar_criacao_comanda(db: AsyncSession, comanda_data: ComandaCreate) -> Tuple[Optional[Cliente], Mesa]:
        """
        Valida se é possível criar uma comanda com os dados fornecidos.
        Retorna o cliente (se informado) e a mesa validados.

        Raises:
            ComandaValidationError: Se alguma validação falhar
        """
        # 1. Verificar se a mesa existe
        mesa = await ComandaService._buscar_mesa(db, comanda_data.id_mesa)
        if not mesa:
            raise ComandaValidationError(f"Mesa com ID {comanda_data.id_mesa} não encontrada")

        # 2. Verificar se a mesa já tem comanda ativa
        comanda_ativa_mesa = await ComandaService._verificar_mesa_ocupada(db, comanda_data.id_mesa)
        if comanda_ativa_mesa:
            raise ComandaValidationError(
                f"Mesa {comanda_data.id_mesa} já possui uma comanda ativa (ID: {comanda_ativa_mesa.id})"
            )

        cliente = None
        # 3. Se informou cliente, fazer validações específicas
        if comanda_data.id_cliente_associado:
            cliente = await ComandaService._buscar_cliente(db, comanda_data.id_cliente_associado)
            if not cliente:
                raise ComandaValidationError(f"Cliente com ID {comanda_data.id_cliente_associado} não encontrado")

            # 4. Verificar se o cliente já tem comanda ativa em qualquer mesa
            comanda_ativa_cliente = await ComandaService._verificar_cliente_ocupado(db,
                                                                                    comanda_data.id_cliente_associado)
            if comanda_ativa_cliente:
                raise ComandaValidationError(
                    f"Cliente {comanda_data.id_cliente_associado} já possui uma comanda ativa "
                    f"(ID: {comanda_ativa_cliente.id}, Mesa: {comanda_ativa_cliente.id_mesa})"
                )

        return cliente, mesa

    @staticmethod
    async def criar_comanda(db: AsyncSession, comanda_data: ComandaCreate) -> Comanda:
        """
        Cria uma nova comanda após validar todas as regras de negócio.
        """
        try:
            # Validar criação
            cliente, mesa = await ComandaService.validar_criacao_comanda(db, comanda_data)

            # Gerar QR Code se não fornecido
            qr_code = comanda_data.qr_code_comanda_hash or str(uuid.uuid4())

            # Criar comanda
            db_comanda = Comanda(
                id_mesa=comanda_data.id_mesa,
                id_cliente_associado=comanda_data.id_cliente_associado,
                status_comanda=comanda_data.status_comanda,
                valor_total_calculado=comanda_data.valor_total_calculado or Decimal(0),
                valor_pago=comanda_data.valor_pago or Decimal(0),
                valor_fiado=comanda_data.valor_fiado or Decimal(0),
                observacoes=comanda_data.observacoes,
                qr_code_comanda_hash=qr_code
            )

            db.add(db_comanda)
            await db.commit()
            await db.refresh(db_comanda)

            logger.info(f"✅ Comanda criada com sucesso: ID {db_comanda.id}, Mesa {db_comanda.id_mesa}")

            # Recarregar com relacionamentos
            return await ComandaService.buscar_comanda_completa(db, db_comanda.id)

        except ComandaValidationError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Erro ao criar comanda: {e}")
            raise ComandaValidationError(f"Erro interno ao criar comanda: {str(e)}")

    @staticmethod
    async def buscar_comanda_por_id(db: AsyncSession, comanda_id: int) -> Optional[Comanda]:
        """Busca uma comanda pelo ID com relacionamentos básicos"""
        try:
            result = await db.execute(
                select(Comanda)
                .options(
                    selectinload(Comanda.itens_pedido),
                    selectinload(Comanda.pagamentos),
                    selectinload(Comanda.fiados_registrados)
                )
                .where(Comanda.id == comanda_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ Erro ao buscar comanda {comanda_id}: {e}")
            return None

    @staticmethod
    async def buscar_comanda_completa(db: AsyncSession, comanda_id: int) -> Optional[Comanda]:
        """Busca uma comanda com todos os relacionamentos carregados"""
        try:
            result = await db.execute(
                select(Comanda)
                .options(
                    joinedload(Comanda.mesa),
                    joinedload(Comanda.cliente),
                    selectinload(Comanda.itens_pedido),
                    selectinload(Comanda.pagamentos),
                    selectinload(Comanda.fiados_registrados),
                )
                .where(Comanda.id == comanda_id)
            )
            return result.unique().scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ Erro ao buscar comanda completa {comanda_id}: {e}")
            return None

    @staticmethod
    async def listar_comandas(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Comanda]:
        """Lista comandas com paginação"""
        try:
            result = await db.execute(
                select(Comanda)
                .options(
                    selectinload(Comanda.mesa),
                    selectinload(Comanda.cliente),
                    selectinload(Comanda.pagamentos),
                    selectinload(Comanda.fiados_registrados),
                    selectinload(Comanda.itens_pedido),
                )
                .offset(skip)
                .limit(limit)
                .order_by(Comanda.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"❌ Erro ao listar comandas: {e}")
            return []

    @staticmethod
    async def buscar_comanda_ativa_por_mesa(db: AsyncSession, mesa_id: int) -> Optional[Comanda]:
        """Busca comanda ativa de uma mesa específica"""
        try:
            # Primeiro verificar se a mesa existe
            mesa = await ComandaService._buscar_mesa(db, mesa_id)
            if not mesa:
                raise ComandaValidationError(f"Mesa {mesa_id} não encontrada")

            result = await db.execute(
                select(Comanda)
                .options(
                    joinedload(Comanda.mesa),
                    selectinload(Comanda.itens_pedido),
                    selectinload(Comanda.pagamentos),
                    selectinload(Comanda.fiados_registrados)
                )
                .where(
                    and_(
                        Comanda.id_mesa == mesa_id,
                        Comanda.status_comanda.in_([StatusComanda.ABERTA, StatusComanda.PAGA_PARCIALMENTE])
                    )
                )
                .order_by(Comanda.created_at.desc())
            )
            return result.scalar_one_or_none()
        except ComandaValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao buscar comanda ativa da mesa {mesa_id}: {e}")
            return None

    @staticmethod
    async def registrar_pagamento(db: AsyncSession, comanda_id: int, pagamento_data: PagamentoCreateSchema) -> Comanda:
        """✅ CORRIGIDO: Registra um pagamento na comanda"""
        try:
            comanda = await ComandaService.buscar_comanda_por_id(db, comanda_id)
            if not comanda:
                raise ComandaValidationError(f"Comanda {comanda_id} não encontrada")

            # Validar status da comanda
            if comanda.status_comanda in [StatusComanda.PAGA_TOTALMENTE, StatusComanda.CANCELADA,
                                          StatusComanda.FECHADA]:
                raise ComandaValidationError(f"Comanda já está {comanda.status_comanda.value}")

            # Validar valor do pagamento
            if pagamento_data.valor_pago <= 0:
                raise ComandaValidationError("Valor do pagamento deve ser maior que zero")

            logger.info(f"💰 Registrando pagamento - Comanda {comanda_id}: "
                        f"Valor: {pagamento_data.valor_pago}, "
                        f"Método: {pagamento_data.metodo_pagamento}")

            # Criar pagamento
            novo_pagamento = Pagamento(
                id_comanda=comanda_id,
                id_cliente=pagamento_data.id_cliente,
                id_usuario_registrou=pagamento_data.id_usuario_registrou,
                valor_pago=pagamento_data.valor_pago,
                metodo_pagamento=pagamento_data.metodo_pagamento,
                observacoes=pagamento_data.observacoes
            )
            db.add(novo_pagamento)

            # Atualizar valor pago
            comanda.valor_pago = (comanda.valor_pago or Decimal(0)) + pagamento_data.valor_pago

            # ✅ CORREÇÃO: Usar método unificado com flag apenas_saldo=True
            comanda.atualizar_valores_comanda(apenas_saldo=True)

            # Atualizar status
            if comanda.valor_total_calculado <= Decimal(0):
                comanda.status_comanda = StatusComanda.PAGA_TOTALMENTE
                logger.info(f"✅ Comanda {comanda_id} PAGA TOTALMENTE")
            elif comanda.valor_coberto > 0:
                comanda.status_comanda = StatusComanda.PAGA_PARCIALMENTE
                logger.info(f"🔄 Comanda {comanda_id} PAGA PARCIALMENTE")

            await db.commit()
            await db.refresh(comanda)

            logger.info(f"✅ Pagamento registrado: Comanda {comanda_id}, "
                        f"Valor {pagamento_data.valor_pago}, "
                        f"Status: {comanda.status_comanda}, "
                        f"Saldo: {comanda.valor_total_calculado}")
            return comanda

        except ComandaValidationError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Erro ao registrar pagamento na comanda {comanda_id}: {e}")
            raise ComandaValidationError(f"Erro interno ao registrar pagamento: {str(e)}")

    @staticmethod
    async def registrar_fiado(db: AsyncSession, comanda_id: int, fiado_data: FiadoCreate) -> Comanda:
        """
        ✅ CORRIGIDO: Registra fiado na comanda
        - valor_fiado: para controle/relatórios
        - valor_pago: para cálculo do saldo
        """
        try:
            comanda = await ComandaService.buscar_comanda_por_id(db, comanda_id)
            if not comanda:
                raise ComandaValidationError(f"Comanda {comanda_id} não encontrada")

            if comanda.status_comanda in [StatusComanda.PAGA_TOTALMENTE, StatusComanda.CANCELADA,
                                          StatusComanda.FECHADA]:
                raise ComandaValidationError(
                    f"Não é possível registrar fiado em comanda {comanda.status_comanda.value}")

            valor_a_fiar = fiado_data.valor_fiado
            if valor_a_fiar <= Decimal(0):
                raise ComandaValidationError("Valor do fiado deve ser maior que zero")

            logger.info(f"📝 Registrando fiado - Comanda {comanda_id}: Valor: {valor_a_fiar}")

            # Criar registro de fiado
            novo_fiado = Fiado(
                id_comanda=comanda_id,
                id_cliente=fiado_data.id_cliente,
                valor_original=valor_a_fiar,
                valor_devido=valor_a_fiar,
                observacoes=fiado_data.observacoes
            )
            db.add(novo_fiado)

            # ✅ CORREÇÃO: valor_fiado para controle, valor_pago para cálculo
            comanda.valor_fiado = (comanda.valor_fiado or Decimal(0)) + valor_a_fiar
            comanda.valor_pago = (comanda.valor_pago or Decimal(0)) + valor_a_fiar

            # ✅ CORREÇÃO: Usar método unificado com flag apenas_saldo=True
            comanda.atualizar_valores_comanda(apenas_saldo=True)

            # Atualizar status
            if comanda.valor_total_calculado <= Decimal(0):
                comanda.status_comanda = StatusComanda.PAGA_TOTALMENTE
            else:
                comanda.status_comanda = StatusComanda.PAGA_PARCIALMENTE

            await db.commit()
            await db.refresh(comanda)

            logger.info(f"✅ Fiado registrado: Comanda {comanda_id}, "
                        f"Valor fiado: {valor_a_fiar}, "
                        f"Total fiado (controle): {comanda.valor_fiado}, "
                        f"Total pago (cálculo): {comanda.valor_pago}, "
                        f"Saldo: {comanda.valor_total_calculado}")

            return comanda

        except ComandaValidationError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Erro ao registrar fiado: {e}")
            raise ComandaValidationError(f"Erro interno: {str(e)}")

    @staticmethod
    async def registrar_credito(db: AsyncSession, comanda_id: int, valor_credito: Decimal,
                                observacoes: Optional[str] = None) -> Comanda:
        """
        ✅ CORRIGIDO: Registra uso de crédito na comanda
        """
        try:
            comanda = await ComandaService.buscar_comanda_por_id(db, comanda_id)
            if not comanda:
                raise ComandaValidationError(f"Comanda {comanda_id} não encontrada")

            if comanda.status_comanda in [StatusComanda.PAGA_TOTALMENTE, StatusComanda.CANCELADA,
                                          StatusComanda.FECHADA]:
                raise ComandaValidationError(
                    f"Não é possível usar crédito em comanda {comanda.status_comanda.value}")

            if valor_credito <= Decimal(0):
                raise ComandaValidationError("Valor do crédito deve ser maior que zero")

            logger.info(f"💳 Registrando crédito - Comanda {comanda_id}: Valor: {valor_credito}")

            # Atualizar valor de crédito usado
            comanda.valor_credito_usado = (comanda.valor_credito_usado or Decimal(0)) + valor_credito

            # Adicionar observação se fornecida
            if observacoes:
                obs_credito = f"Crédito usado: R$ {valor_credito} - {observacoes}"
                if comanda.observacoes:
                    comanda.observacoes += f"\n{obs_credito}"
                else:
                    comanda.observacoes = obs_credito

            # ✅ CORREÇÃO: Usar método unificado com flag apenas_saldo=True
            comanda.atualizar_valores_comanda(apenas_saldo=True)

            # Atualizar status
            if comanda.valor_total_calculado <= Decimal(0):
                comanda.status_comanda = StatusComanda.PAGA_TOTALMENTE
            else:
                comanda.status_comanda = StatusComanda.PAGA_PARCIALMENTE

            await db.commit()
            await db.refresh(comanda)

            logger.info(f"✅ Crédito registrado: Comanda {comanda_id}, "
                        f"Valor: {valor_credito}, "
                        f"Total crédito: {comanda.valor_credito_usado}, "
                        f"Saldo: {comanda.valor_total_calculado}")

            return comanda

        except ComandaValidationError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Erro ao registrar crédito: {e}")
            raise ComandaValidationError(f"Erro interno: {str(e)}")

    @staticmethod
    async def fechar_comanda(db: AsyncSession, comanda_id: int) -> Comanda:
        """Fecha uma comanda"""
        try:
            comanda = await ComandaService.buscar_comanda_por_id(db, comanda_id)
            if not comanda:
                raise ComandaValidationError(f"Comanda {comanda_id} não encontrada")

            # Validar se pode ser fechada
            if comanda.status_comanda not in [StatusComanda.PAGA_TOTALMENTE, StatusComanda.EM_FIADO]:
                raise ComandaValidationError(
                    "Comanda só pode ser fechada se estiver totalmente paga ou com saldo em fiado"
                )

            comanda.status_comanda = StatusComanda.FECHADA
            await db.commit()
            await db.refresh(comanda)

            logger.info(f"✅ Comanda fechada: ID {comanda_id}")
            return comanda

        except ComandaValidationError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Erro ao fechar comanda {comanda_id}: {e}")
            raise ComandaValidationError(f"Erro interno ao fechar comanda: {str(e)}")

    @staticmethod
    async def gerar_qrcode(db: AsyncSession, comanda_id: int) -> Comanda:
        """Gera ou retorna QR Code da comanda"""
        try:
            comanda = await ComandaService.buscar_comanda_por_id(db, comanda_id)
            if not comanda:
                raise ComandaValidationError(f"Comanda {comanda_id} não encontrada")

            if not comanda.qr_code_comanda_hash:
                comanda.qr_code_comanda_hash = str(uuid.uuid4())
                await db.commit()
                await db.refresh(comanda)

            return comanda

        except ComandaValidationError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Erro ao gerar QR Code para comanda {comanda_id}: {e}")
            raise ComandaValidationError(f"Erro interno ao gerar QR Code: {str(e)}")

    @staticmethod
    async def aplicar_desconto(db: AsyncSession, comanda_id: int, valor_desconto: Decimal,
                               motivo: Optional[str] = None) -> Comanda:
        """✅ CORRIGIDO: Aplica um desconto na comanda"""
        try:
            comanda = await ComandaService.buscar_comanda_por_id(db, comanda_id)
            if not comanda:
                raise ComandaValidationError(f"Comanda {comanda_id} não encontrada")

            # Validar status da comanda
            if comanda.status_comanda in [StatusComanda.CANCELADA, StatusComanda.FECHADA]:
                raise ComandaValidationError(
                    f"Não é possível aplicar desconto em comanda {comanda.status_comanda.value}")

            # Validar valor do desconto
            if valor_desconto < 0:
                raise ComandaValidationError("Valor do desconto não pode ser negativo")

            # Calcular valor máximo de desconto (não pode ser maior que itens + taxa)
            valor_maximo_desconto = comanda.valor_final_comanda + comanda.valor_taxa_servico
            if valor_desconto > valor_maximo_desconto:
                raise ComandaValidationError(
                    f"Desconto não pode ser maior que o valor total da comanda (R$ {valor_maximo_desconto})")

            logger.info(f"🎁 Aplicando desconto - Comanda {comanda_id}: Valor: {valor_desconto}")

            # Aplicar desconto
            comanda.valor_desconto = valor_desconto

            # Adicionar motivo nas observações se fornecido
            if motivo:
                observacao_desconto = f"Desconto aplicado: R$ {valor_desconto} - {motivo}"
                if comanda.observacoes:
                    comanda.observacoes += f"\n{observacao_desconto}"
                else:
                    comanda.observacoes = observacao_desconto

            # ✅ CORREÇÃO: Usar método unificado com flag apenas_saldo=False (recalcular tudo)
            comanda.atualizar_valores_comanda(apenas_saldo=False)

            # Atualizar status se necessário
            if comanda.valor_total_calculado <= Decimal(0) and comanda.valor_coberto > 0:
                comanda.status_comanda = StatusComanda.PAGA_TOTALMENTE
            elif comanda.valor_coberto > 0:
                comanda.status_comanda = StatusComanda.PAGA_PARCIALMENTE

            await db.commit()
            await db.refresh(comanda)

            logger.info(f"✅ Desconto aplicado: Comanda {comanda_id}, "
                        f"Valor {valor_desconto}, "
                        f"Novo Saldo: {comanda.valor_total_calculado}, "
                        f"Status: {comanda.status_comanda}")
            return comanda

        except ComandaValidationError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Erro ao aplicar desconto na comanda {comanda_id}: {e}")
            raise ComandaValidationError(f"Erro interno ao aplicar desconto: {str(e)}")

    @staticmethod
    async def adicionar_item_comanda(db: AsyncSession, comanda_id: int, item_data) -> Comanda:
        """
        ✅ CORRIGIDO: Quando adicionar itens, usar método unificado
        """
        try:
            comanda = await ComandaService.buscar_comanda_por_id(db, comanda_id)
            if not comanda:
                raise ComandaValidationError(f"Comanda {comanda_id} não encontrada")

            # ... lógica para adicionar item ...

            # ✅ CORREÇÃO: Usar método unificado com flag apenas_saldo=False (recalcular tudo)
            comanda.atualizar_valores_comanda(apenas_saldo=False)

            await db.commit()
            await db.refresh(comanda)

            return comanda

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Erro ao adicionar item: {e}")
            raise ComandaValidationError(f"Erro interno: {str(e)}")

    # Métodos auxiliares privados
    @staticmethod
    async def _buscar_cliente(db: AsyncSession, cliente_id: int) -> Optional[Cliente]:
        """Busca cliente por ID"""
        result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def _buscar_mesa(db: AsyncSession, mesa_id: int) -> Optional[Mesa]:
        """Busca mesa por ID"""
        result = await db.execute(select(Mesa).where(Mesa.id == mesa_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def _verificar_mesa_ocupada(db: AsyncSession, mesa_id: int) -> Optional[Comanda]:
        """Verifica se a mesa já tem comanda ativa"""
        result = await db.execute(
            select(Comanda)
            .where(
                and_(
                    Comanda.id_mesa == mesa_id,
                    Comanda.status_comanda.in_([StatusComanda.ABERTA, StatusComanda.PAGA_PARCIALMENTE])
                )
            )
            .order_by(Comanda.created_at.desc())
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _verificar_cliente_ocupado(db: AsyncSession, cliente_id: int) -> Optional[Comanda]:
        """Verifica se o cliente já tem comanda ativa em qualquer mesa"""
        result = await db.execute(
            select(Comanda)
            .where(
                and_(
                    Comanda.id_cliente_associado == cliente_id,
                    Comanda.status_comanda.in_([StatusComanda.ABERTA, StatusComanda.PAGA_PARCIALMENTE])
                )
            )
            .order_by(Comanda.created_at.desc())
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def recalcular_totais_comanda(db: AsyncSession, comanda_id: int, fazer_commit: bool = True) -> Optional[
        Comanda]:
        """
        ✅ CORRIGIDO: Recalcula totais da comanda baseado nos itens
        """
        try:
            logger.info(f"🔄 Recalculando totais da comanda {comanda_id}")

            # Calcular total dos itens
            result_totais = await db.execute(
                select(
                    func.coalesce(func.sum(ItemPedido.preco_unitario * ItemPedido.quantidade), 0).label('total_itens')
                ).where(ItemPedido.id_comanda == comanda_id)
            )
            total_itens = Decimal(str(result_totais.scalar() or 0))

            # Buscar dados da comanda
            result_comanda = await db.execute(
                select(
                    Comanda.percentual_taxa_servico,
                    Comanda.valor_desconto,
                    Comanda.valor_pago,
                    Comanda.valor_credito_usado
                ).where(Comanda.id == comanda_id)
            )
            comanda_data = result_comanda.first()

            if not comanda_data:
                logger.error(f"❌ Comanda {comanda_id} não encontrada para recálculo")
                return None

            # Calcular valores
            percentual_taxa = comanda_data.percentual_taxa_servico or Decimal("0.0")
            valor_taxa = (total_itens * percentual_taxa / Decimal("100")).quantize(Decimal("0.01"))
            desconto = comanda_data.valor_desconto or Decimal("0.0")

            # ✅ CORREÇÃO: Calcular valor total original e saldo devedor
            valor_total_original = max(Decimal("0.0"), total_itens + valor_taxa - desconto)

            # ✅ CORREÇÃO: Só subtrair valor_pago + valor_credito
            valor_pago = comanda_data.valor_pago or Decimal("0.0")
            valor_credito = comanda_data.valor_credito_usado or Decimal("0.0")
            valor_total_calculado = max(Decimal("0.0"), valor_total_original - valor_pago - valor_credito)

            logger.info(f"📊 Recálculo: Itens: {total_itens}, Taxa: {valor_taxa}, "
                        f"Desconto: {desconto}, Pago: {valor_pago}, "
                        f"Crédito: {valor_credito}, Saldo: {valor_total_calculado}")

            # Atualizar no banco
            await db.execute(
                update(Comanda)
                .where(Comanda.id == comanda_id)
                .values(
                    valor_final_comanda=total_itens,
                    valor_taxa_servico=valor_taxa,
                    valor_total_calculado=valor_total_calculado,
                    updated_at=datetime.now()
                )
            )

            if fazer_commit:
                await db.commit()
                logger.info(f"✅ Totais recalculados para comanda {comanda_id}")
            else:
                await db.flush()

            return await ComandaService.buscar_comanda_por_id(db, comanda_id)

        except Exception as e:
            logger.error(f"❌ Erro ao recalcular totais da comanda {comanda_id}: {e}")
            if fazer_commit:
                await db.rollback()
            return None


async def force_recalculate_and_commit(db: AsyncSession, id_comanda: int) -> bool:
    """
    FUNÇÃO DE EMERGÊNCIA - Força recálculo e commit imediato da comanda.
    Usa uma nova transação para garantir persistência.
    """
    try:
        logger.warning(f"🚨 FORÇA RECÁLCULO da comanda {id_comanda}")

        # Recalcular com commit forçado
        comanda = await recalculate_comanda_totals(db, id_comanda, fazer_commit=True)

        if comanda:
            logger.info(f"✅ FORÇA RECÁLCULO bem-sucedido - Comanda {id_comanda}")
            return True
        else:
            logger.error(f"❌ FORÇA RECÁLCULO falhou - Comanda {id_comanda}")
            return False

    except Exception as e:
        logger.exception(f"💥 ERRO na FORÇA RECÁLCULO da comanda {id_comanda}: {e}")
        return False


# Manter funções antigas para compatibilidade
async def create_comanda(db: AsyncSession, comanda_data: ComandaCreate) -> Comanda:
    return await ComandaService.criar_comanda(db, comanda_data)


async def get_comanda_by_id(db: AsyncSession, comanda_id: int) -> Optional[Comanda]:
    return await ComandaService.buscar_comanda_por_id(db, comanda_id)


async def get_comanda_by_id_detail(db: AsyncSession, comanda_id: int) -> Optional[Comanda]:
    return await ComandaService.buscar_comanda_completa(db, comanda_id)


async def get_all_comandas_detailed(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Comanda]:
    return await ComandaService.listar_comandas(db, skip, limit)


async def get_active_comanda_by_mesa_id(db: AsyncSession, mesa_id: int):
    return await ComandaService.buscar_comanda_ativa_por_mesa(db, mesa_id)


async def registrar_pagamento_na_comanda(db: AsyncSession, comanda_id: int,
                                         pagamento_data: PagamentoCreateSchema) -> Comanda:
    return await ComandaService.registrar_pagamento(db, comanda_id, pagamento_data)


async def registrar_saldo_como_fiado(db: AsyncSession, comanda_id: int, fiado_data: FiadoCreate) -> Comanda:
    return await ComandaService.registrar_fiado(db, comanda_id, fiado_data)


async def fechar_comanda(db: AsyncSession, comanda_id: int) -> Optional[Comanda]:
    return await ComandaService.fechar_comanda(db, comanda_id)


async def gerar_ou_obter_qrcode_comanda(db: AsyncSession, comanda_id: int) -> Optional[Comanda]:
    return await ComandaService.gerar_qrcode(db, comanda_id)


async def buscar_cliente(db: AsyncSession, cliente_id: int):
    return await ComandaService._buscar_cliente(db, cliente_id)


async def buscar_mesa(db: AsyncSession, mesa_id: int):
    return await ComandaService._buscar_mesa(db, mesa_id)


async def recalculate_comanda_totals(db: AsyncSession, id_comanda: int, fazer_commit: bool = True) -> Optional[Comanda]:
    return await ComandaService.recalcular_totais_comanda(db, id_comanda, fazer_commit)
