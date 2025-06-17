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


def sanitizar_valores_monetarios_sync(comanda: Comanda) -> None:
    """✅ FUNÇÃO SÍNCRONA para sanitizar valores monetários"""
    if not comanda:
        return

    campos_monetarios = [
        'valor_total_calculado', 'percentual_taxa_servico', 'valor_taxa_servico',
        'valor_desconto', 'valor_final_comanda', 'valor_pago', 'valor_fiado', 'valor_credito_usado'
    ]

    for campo in campos_monetarios:
        valor = getattr(comanda, campo, None)
        if valor is None:
            setattr(comanda, campo, Decimal("0.00"))
        elif not isinstance(valor, Decimal):
            try:
                setattr(comanda, campo, Decimal(str(valor)))
            except (ValueError, TypeError):
                setattr(comanda, campo, Decimal("0.00"))


class ComandaService:
    """Service responsável por toda lógica de negócio relacionada a comandas"""

    @staticmethod
    async def validar_criacao_comanda(db: AsyncSession, comanda_data: ComandaCreate) -> Tuple[Optional[Cliente], Mesa]:
        """
        Valida se é possível criar uma comanda com os dados fornecidos.
        Retorna o cliente (se informado) e a mesa validados.
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
        """Cria uma nova comanda após validar todas as regras de negócio."""
        try:
            # Validar criação
            cliente, mesa = await ComandaService.validar_criacao_comanda(db, comanda_data)

            # Gerar QR Code se não fornecido
            qr_code = comanda_data.qr_code_comanda_hash or str(uuid.uuid4())

            # ✅ CORRIGIDO: Garantir que todos os valores sejam Decimal
            db_comanda = Comanda(
                id_mesa=comanda_data.id_mesa,
                id_cliente_associado=comanda_data.id_cliente_associado,
                status_comanda=comanda_data.status_comanda,
                valor_total_calculado=Decimal(str(comanda_data.valor_total_calculado or "0.00")),
                percentual_taxa_servico=Decimal(str(comanda_data.percentual_taxa_servico or "10.00")),
                valor_taxa_servico=Decimal(str(comanda_data.valor_taxa_servico or "0.00")),
                valor_desconto=Decimal(str(comanda_data.valor_desconto or "0.00")),
                valor_final_comanda=Decimal(str(comanda_data.valor_final_comanda or "0.00")),
                valor_pago=Decimal(str(comanda_data.valor_pago or "0.00")),
                valor_fiado=Decimal(str(comanda_data.valor_fiado or "0.00")),
                valor_credito_usado=Decimal(str(comanda_data.valor_credito_usado or "0.00")),
                observacoes=comanda_data.observacoes,
                qr_code_comanda_hash=qr_code
            )

            db.add(db_comanda)
            await db.commit()
            await db.refresh(db_comanda)

            logger.info(f"✅ Comanda criada com sucesso: ID {db_comanda.id}, Mesa {db_comanda.id_mesa}")

            # ✅ CORRIGIDO: Recarregar com relacionamentos para retornar dados completos
            return await ComandaService.buscar_comanda_completa(db, db_comanda.id)

        except ComandaValidationError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Erro ao criar comanda: {e}")
            raise ComandaValidationError(f"Erro interno ao criar comanda: {str(e)}")



    @staticmethod
    async def buscar_comanda_por_id(db: AsyncSession, comanda_id: int) -> Optional[Comanda]:
        """Busca uma comanda pelo ID com todos os relacionamentos necessários

        Args:
            db: Sessão assíncrona do banco de dados
            comanda_id: ID da comanda a ser buscada

        Returns:
            Objeto Comanda com relacionamentos ou None se não encontrado
        """
        try:
            logger.debug(f"🔍 Buscando comanda {comanda_id} com relacionamentos")

            # Carrega a comanda com todos os relacionamentos necessários
            query = (
                select(Comanda)
                .where(Comanda.id == comanda_id)
                .options(
                    selectinload(Comanda.mesa),  # Adicionado se existir
                    selectinload(Comanda.cliente),  # Adicionado se existir
                    selectinload(Comanda.itens_pedido),
                    selectinload(Comanda.pagamentos),
                    selectinload(Comanda.fiados_registrados)
                )
            )

            result = await db.execute(query)
            comanda = result.scalar_one_or_none()

            if not comanda:
                logger.warning(f"⚠️ Comanda {comanda_id} não encontrada")
                return None

            # Garante que valores monetários tenham defaults adequados
            comanda.valor_total_calculado = comanda.valor_total_calculado or Decimal('0.00')
            comanda.valor_taxa_servico = comanda.valor_taxa_servico or Decimal('0.00')
            # ... outros campos monetários

            logger.debug(f"✅ Comanda {comanda_id} carregada com sucesso")
            return comanda

        except MultipleResultsFound:
            logger.error(f"❌ Múltiplas comandas encontradas para o ID {comanda_id}")
            return None
        except SQLAlchemyError as e:
            logger.error(f"❌ Erro de banco de dados ao buscar comanda {comanda_id}: {str(e)}")
            await db.rollback()
            return None
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao buscar comanda {comanda_id}: {str(e)}", exc_info=True)
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
                    selectinload(Comanda.itens_pedido).joinedload(ItemPedido.produto),  # ✅ corrigido aqui
                    selectinload(Comanda.pagamentos),
                    selectinload(Comanda.fiados_registrados),
                )
                .where(Comanda.id == comanda_id)
            )
            comanda = result.unique().scalar_one_or_none()

            if comanda:
                sanitizar_valores_monetarios_sync(comanda)

            return comanda

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
                    # ==========================================================
                    # ALTERAÇÃO PRINCIPAL AQUI: Carregando o produto dentro do item
                    # ==========================================================
                    selectinload(Comanda.itens_pedido).selectinload(ItemPedido.produto)
                )
                .offset(skip)
                .limit(limit)
                .order_by(Comanda.created_at.desc())
            )
            comandas = result.scalars().all()

            # Esta parte agora deve funcionar sem erros
            for comanda in comandas:
                sanitizar_valores_monetarios_sync(comanda)

            return comandas
        except Exception as e:
            logger.error(f"❌ Erro ao listar comandas: {e}")
            return []

    @staticmethod
    async def buscar_comanda_ativa_por_mesa(db: AsyncSession, mesa_id: int) -> Optional[Comanda]:
        """✅ CORRIGIDO: Busca comanda ativa de uma mesa específica"""
        try:
            # Primeiro verificar se a mesa existe
            mesa = await ComandaService._buscar_mesa(db, mesa_id)
            if not mesa:
                raise ComandaValidationError(f"Mesa {mesa_id} não encontrada")

            result = await db.execute(
                select(Comanda)
                .options(
                    joinedload(Comanda.mesa),
                    joinedload(Comanda.cliente),
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
            comanda = result.unique().scalar_one_or_none()

            # ✅ CORRIGIDO: Usar função síncrona
            if comanda:
                sanitizar_valores_monetarios_sync(comanda)

            return comanda
        except ComandaValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao buscar comanda ativa da mesa {mesa_id}: {e}")
            return None

    @staticmethod
    async def registrar_pagamento(db: AsyncSession, comanda_id: int, pagamento_data: PagamentoCreateSchema) -> Comanda:
        """Registra um pagamento na comanda com suporte a saldo_credito"""
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

            # ✅ CORRIGIDO: Calcular manualmente
            valor_total_original = (comanda.valor_final_comanda or Decimal(0)) + (
                        comanda.valor_taxa_servico or Decimal(0)) - (comanda.valor_desconto or Decimal(0))
            valor_coberto = (comanda.valor_pago or Decimal(0)) + (comanda.valor_credito_usado or Decimal(0))
            comanda.valor_total_calculado = max(Decimal(0), valor_total_original - valor_coberto)

            # Verificar se há pagamento excedente e cliente para creditar
            cliente = None
            if comanda.valor_total_calculado < Decimal(0) and comanda.id_cliente_associado:
                # Buscar cliente diretamente do banco para garantir que está na sessão atual
                cliente_id = comanda.id_cliente_associado
                result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
                cliente = result.scalar_one_or_none()

                if cliente:
                    # Valor negativo indica pagamento excedente
                    valor_excedente = abs(comanda.valor_total_calculado)

                    # Ajustar o valor total calculado para zero
                    comanda.valor_total_calculado = Decimal(0)

                    # Adicionar o excedente ao saldo de crédito do cliente
                    cliente.saldo_credito = (cliente.saldo_credito or Decimal(0)) + valor_excedente

                    # Registrar nas observações
                    obs_credito = f"Crédito adicionado: R$ {valor_excedente} (pagamento excedente)"
                    if comanda.observacoes:
                        comanda.observacoes += f"\n{obs_credito}"
                    else:
                        comanda.observacoes = obs_credito

                    # Garantir que o cliente seja marcado como modificado
                    await db.execute(
                        update(Cliente)
                        .where(Cliente.id == cliente_id)
                        .values(saldo_credito=cliente.saldo_credito)
                    )

                    logger.info(f"💰 Crédito adicionado ao cliente {cliente.id}: R$ {valor_excedente}")

            # Atualizar status
            if comanda.valor_total_calculado <= Decimal(0):
                comanda.status_comanda = StatusComanda.PAGA_TOTALMENTE
                logger.info(f"✅ Comanda {comanda_id} PAGA TOTALMENTE")
            elif valor_coberto > 0:
                comanda.status_comanda = StatusComanda.PAGA_PARCIALMENTE
                logger.info(f"🔄 Comanda {comanda_id} PAGA PARCIALMENTE")

            # ✅ CORRIGIDO: Usar função síncrona
            sanitizar_valores_monetarios_sync(comanda)

            # Commit para salvar todas as alterações
            await db.commit()

            # Refresh para garantir que os dados estão atualizados
            await db.refresh(comanda)
            if cliente:
                await db.refresh(cliente)

            return comanda

        except ComandaValidationError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Erro ao registrar pagamento na comanda {comanda_id}: {e}")
            raise ComandaValidationError(f"Erro interno ao registrar pagamento: {str(e)}")

    @staticmethod
    async def usar_credito_cliente(db: AsyncSession, comanda_id: int,
                                   valor_credito: Optional[Decimal] = None) -> Comanda:
        """Usa o saldo de crédito do cliente para pagar a comanda"""
        try:
            comanda = await ComandaService.buscar_comanda_por_id(db, comanda_id)
            if not comanda:
                raise ComandaValidationError(f"Comanda {comanda_id} não encontrada")

            # Validar status da comanda
            if comanda.status_comanda in [StatusComanda.PAGA_TOTALMENTE, StatusComanda.CANCELADA,
                                          StatusComanda.FECHADA]:
                raise ComandaValidationError(f"Comanda já está {comanda.status_comanda.value}")

            # Verificar se há cliente associado
            if not comanda.id_cliente_associado:
                raise ComandaValidationError("Comanda não possui cliente associado para usar crédito")

            # Buscar cliente diretamente do banco para garantir que está na sessão atual
            cliente_id = comanda.id_cliente_associado
            result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
            cliente = result.scalar_one_or_none()

            if not cliente:
                raise ComandaValidationError(f"Cliente ID {comanda.id_cliente_associado} não encontrado")

            # Verificar se cliente tem saldo de crédito
            if not cliente.saldo_credito or cliente.saldo_credito <= 0:
                raise ComandaValidationError(f"Cliente não possui saldo de crédito disponível")

            # Determinar valor a ser usado
            saldo_devedor = comanda.valor_total_calculado
            saldo_credito_cliente = cliente.saldo_credito

            if valor_credito is None:
                # Usar todo o saldo disponível até o valor da comanda
                valor_a_usar = min(saldo_devedor, saldo_credito_cliente)
            else:
                # Usar valor específico
                if valor_credito <= 0:
                    raise ComandaValidationError("Valor de crédito a usar deve ser maior que zero")
                if valor_credito > saldo_credito_cliente:
                    raise ComandaValidationError(
                        f"Valor solicitado (R$ {valor_credito}) excede o saldo de crédito disponível (R$ {saldo_credito_cliente})")
                valor_a_usar = min(valor_credito, saldo_devedor)

            logger.info(f"💳 Usando crédito do cliente {cliente.id} - Comanda {comanda_id}: Valor: {valor_a_usar}")

            # Atualizar saldo de crédito do cliente
            cliente.saldo_credito -= valor_a_usar

            # Garantir que o cliente seja marcado como modificado
            await db.execute(
                update(Cliente)
                .where(Cliente.id == cliente_id)
                .values(saldo_credito=cliente.saldo_credito)
            )

            # Atualizar valor de crédito usado na comanda
            comanda.valor_credito_usado = (comanda.valor_credito_usado or Decimal(0)) + valor_a_usar

            # Adicionar observação
            obs_credito = f"Crédito usado: R$ {valor_a_usar} do saldo do cliente"
            if comanda.observacoes:
                comanda.observacoes += f"\n{obs_credito}"
            else:
                comanda.observacoes = obs_credito

            # ✅ CORRIGIDO: Calcular manualmente
            valor_total_original = (comanda.valor_final_comanda or Decimal(0)) + (
                        comanda.valor_taxa_servico or Decimal(0)) - (comanda.valor_desconto or Decimal(0))
            valor_coberto = (comanda.valor_pago or Decimal(0)) + (comanda.valor_credito_usado or Decimal(0))
            comanda.valor_total_calculado = max(Decimal(0), valor_total_original - valor_coberto)

            # Atualizar status
            if comanda.valor_total_calculado <= Decimal(0):
                comanda.status_comanda = StatusComanda.PAGA_TOTALMENTE
            else:
                comanda.status_comanda = StatusComanda.PAGA_PARCIALMENTE

            # ✅ CORRIGIDO: Usar função síncrona
            sanitizar_valores_monetarios_sync(comanda)

            # Commit para salvar todas as alterações
            await db.commit()

            # Refresh para garantir que os dados estão atualizados
            await db.refresh(comanda)
            await db.refresh(cliente)

            return comanda

        except ComandaValidationError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Erro ao usar crédito do cliente: {e}")
            raise ComandaValidationError(f"Erro interno: {str(e)}")

    @staticmethod
    async def registrar_fiado(db: AsyncSession, comanda_id: int, fiado_data: FiadoCreate) -> Comanda:
        """
        ✅ CORRIGIDO: Registra fiado na comanda - COMPATÍVEL COM NOVO SCHEMA
        """
        try:
            comanda = await ComandaService.buscar_comanda_por_id(db, comanda_id)
            if not comanda:
                raise ComandaValidationError(f"Comanda {comanda_id} não encontrada")

            if comanda.status_comanda in [StatusComanda.PAGA_TOTALMENTE, StatusComanda.CANCELADA,
                                          StatusComanda.FECHADA]:
                raise ComandaValidationError(
                    f"Não é possível registrar fiado em comanda {comanda.status_comanda.value}")

            # ✅ CORRIGIDO: Usar método do schema para obter valor
            valor_a_fiar = fiado_data.get_valor_fiado()
            if not valor_a_fiar or valor_a_fiar <= Decimal(0):
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

            # ✅ CORRIGIDO: Calcular manualmente
            valor_total_original = (comanda.valor_final_comanda or Decimal(0)) + (
                        comanda.valor_taxa_servico or Decimal(0)) - (comanda.valor_desconto or Decimal(0))
            valor_coberto = (comanda.valor_pago or Decimal(0)) + (comanda.valor_credito_usado or Decimal(0))
            comanda.valor_total_calculado = max(Decimal(0), valor_total_original - valor_coberto)

            # Atualizar status
            if comanda.valor_total_calculado <= Decimal(0):
                comanda.status_comanda = StatusComanda.PAGA_TOTALMENTE
            else:
                comanda.status_comanda = StatusComanda.PAGA_PARCIALMENTE

            # ✅ CORRIGIDO: Usar função síncrona
            sanitizar_valores_monetarios_sync(comanda)

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

            # ✅ CORRIGIDO: Calcular manualmente
            valor_total_original = (comanda.valor_final_comanda or Decimal(0)) + (
                        comanda.valor_taxa_servico or Decimal(0)) - (comanda.valor_desconto or Decimal(0))
            valor_coberto = (comanda.valor_pago or Decimal(0)) + (comanda.valor_credito_usado or Decimal(0))
            comanda.valor_total_calculado = max(Decimal(0), valor_total_original - valor_coberto)

            # Atualizar status
            if comanda.valor_total_calculado <= Decimal(0):
                comanda.status_comanda = StatusComanda.PAGA_TOTALMENTE
            else:
                comanda.status_comanda = StatusComanda.PAGA_PARCIALMENTE

            # ✅ CORRIGIDO: Usar função síncrona
            sanitizar_valores_monetarios_sync(comanda)

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
        """Fecha uma comanda com validações de consumo, pedido, pagamento — ou permite se estiver vazia"""
        try:
            comanda = await ComandaService.buscar_comanda_completa(db, comanda_id)
            if not comanda:
                raise ComandaValidationError(f"Comanda {comanda_id} não encontrada")

            # Verificar se já está fechada
            if comanda.status_comanda == StatusComanda.FECHADA:
                raise ComandaValidationError("Esta comanda já está fechada")

            # ✅ NOVA LÓGICA: Verificar se a comanda está vazia
            is_comanda_vazia = (
                    (not hasattr(comanda, 'itens_pedido') or not comanda.itens_pedido or len(
                        comanda.itens_pedido) == 0) and
                    (not hasattr(comanda, 'pagamentos') or not comanda.pagamentos or len(comanda.pagamentos) == 0) and
                    (comanda.valor_final_comanda is None or comanda.valor_final_comanda <= Decimal("0.00"))
            )

            logger.info(f"🔍 Verificando comanda {comanda_id}: "
                        f"Itens: {len(comanda.itens_pedido) if hasattr(comanda, 'itens_pedido') and comanda.itens_pedido else 0}, "
                        f"Pagamentos: {len(comanda.pagamentos) if hasattr(comanda, 'pagamentos') and comanda.pagamentos else 0}, "
                        f"Valor final: {comanda.valor_final_comanda}, "
                        f"Status: {comanda.status_comanda}, "
                        f"Vazia: {is_comanda_vazia}")

            if is_comanda_vazia:
                # ✅ COMANDA VAZIA: Pode ser fechada independente do status
                logger.info(f"📝 Fechando comanda vazia {comanda_id}")
                comanda.status_comanda = StatusComanda.FECHADA
            else:
                # ✅ COMANDA COM ITENS: Validar se está paga ou em fiado
                if comanda.status_comanda not in [StatusComanda.PAGA_TOTALMENTE, StatusComanda.EM_FIADO]:
                    raise ComandaValidationError(
                        "A comanda só pode ser fechada se estiver totalmente paga, com saldo em fiado ou vazia"
                    )

                logger.info(f"💰 Fechando comanda {comanda_id} com status {comanda.status_comanda}")
                comanda.status_comanda = StatusComanda.FECHADA

            # ✅ CORRIGIDO: Usar função síncrona
            sanitizar_valores_monetarios_sync(comanda)

            await db.commit()
            await db.refresh(comanda)

            logger.info(f"✅ Comanda fechada com sucesso: ID {comanda_id}")
            return comanda

        except ComandaValidationError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Erro ao fechar comanda {comanda_id}: {e}")
            raise ComandaValidationError(
                "Erro interno ao tentar fechar a comanda. Tente novamente ou contate o suporte técnico."
            )

    @staticmethod
    async def gerar_qrcode(db: AsyncSession, comanda_id: int) -> Comanda:
        """Gera ou retorna QR Code da comanda"""
        try:
            comanda = await ComandaService.buscar_comanda_por_id(db, comanda_id)
            if not comanda:
                raise ComandaValidationError(f"Comanda {comanda_id} não encontrada")

            if not comanda.qr_code_comanda_hash:
                comanda.qr_code_comanda_hash = str(uuid.uuid4())

                # ✅ CORRIGIDO: Usar função síncrona
                sanitizar_valores_monetarios_sync(comanda)

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
    async def aplicar_desconto(
            db: AsyncSession,
            comanda_id: int,
            valor_desconto: Decimal,
            motivo: Optional[str] = None
    ) -> Comanda:
        """✅ Aplica um desconto na comanda com validações e atualiza os valores."""

        try:
            # Buscar a comanda pelo ID
            comanda = await ComandaService.buscar_comanda_por_id(db, comanda_id)
            if not comanda:
                raise ComandaValidationError(f"Comanda {comanda_id} não encontrada")

            # Validar status da comanda
            if comanda.status_comanda in [StatusComanda.CANCELADA, StatusComanda.FECHADA]:
                raise ComandaValidationError(
                    f"Não é possível aplicar desconto em comanda {comanda.status_comanda.value}"
                )

            # Validar valor do desconto (não negativo)
            if valor_desconto < Decimal("0.00"):
                raise ComandaValidationError("Valor do desconto não pode ser negativo")

            # Calcular valor máximo do desconto (itens + taxa)
            valor_maximo_desconto = (comanda.valor_final_comanda or Decimal("0.00")) + (
                        comanda.valor_taxa_servico or Decimal("0.00"))
            if valor_desconto > valor_maximo_desconto:
                raise ComandaValidationError(
                    f"Desconto não pode ser maior que o valor total da comanda (R$ {valor_maximo_desconto})"
                )

            logger.info(f"🎁 Aplicando desconto - Comanda {comanda_id}: Valor: {valor_desconto}")

            # Aplicar desconto na comanda
            comanda.valor_desconto = valor_desconto

            # Atualizar observações com motivo do desconto
            if motivo:
                observacao_desconto = f"Desconto aplicado: R$ {valor_desconto} - {motivo}"
                if comanda.observacoes:
                    comanda.observacoes += f"\n{observacao_desconto}"
                else:
                    comanda.observacoes = observacao_desconto

            # Recalcular valor total calculado manualmente
            valor_total_original = (
                    (comanda.valor_final_comanda or Decimal("0.00")) +
                    (comanda.valor_taxa_servico or Decimal("0.00")) -
                    (comanda.valor_desconto or Decimal("0.00"))
            )
            valor_coberto = (
                    (comanda.valor_pago or Decimal("0.00")) +
                    (comanda.valor_credito_usado or Decimal("0.00"))
            )
            comanda.valor_total_calculado = max(Decimal("0.00"), valor_total_original - valor_coberto)

            # Atualizar status com base no saldo
            if comanda.valor_total_calculado <= Decimal("0.00") and valor_coberto > Decimal("0.00"):
                comanda.status_comanda = StatusComanda.PAGA_TOTALMENTE
            elif valor_coberto > Decimal("0.00"):
                comanda.status_comanda = StatusComanda.PAGA_PARCIALMENTE

            # Sanitizar valores monetários (função síncrona)
            sanitizar_valores_monetarios_sync(comanda)

            # Commit da transação e refresh para garantir dados atualizados
            await db.commit()
            await db.refresh(comanda)

            logger.info(
                f"✅ Desconto aplicado: Comanda {comanda_id}, "
                f"Valor {valor_desconto}, "
                f"Novo Saldo: {comanda.valor_total_calculado}, "
                f"Status: {comanda.status_comanda}"
            )

            return comanda

        except ComandaValidationError:
            await db.rollback()  # Corrigir rollback em caso de erro customizado também
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Erro ao aplicar desconto na comanda {comanda_id}: {e}", exc_info=True)
            raise ComandaValidationError(f"Erro interno ao aplicar desconto: {str(e)}")




    @staticmethod
    async def adicionar_credito_cliente(db: AsyncSession, cliente_id: int, valor_credito: Decimal,
                                        observacoes: Optional[str] = None) -> Cliente:
        """
        ✅ CORRIGIDO: Adiciona crédito diretamente ao saldo do cliente
        """
        try:
            if valor_credito <= 0:
                raise ComandaValidationError("Valor do crédito deve ser maior que zero")

            # Buscar cliente diretamente do banco para garantir que está na sessão atual
            result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
            cliente = result.scalar_one_or_none()

            if not cliente:
                raise ComandaValidationError(f"Cliente com ID {cliente_id} não encontrado")

            logger.info(f"💰 Adicionando crédito ao cliente {cliente_id}: Valor: {valor_credito}")

            # Atualizar saldo de crédito
            cliente.saldo_credito = (cliente.saldo_credito or Decimal(0)) + valor_credito

            # Garantir que o cliente seja marcado como modificado
            await db.execute(
                update(Cliente)
                .where(Cliente.id == cliente_id)
                .values(saldo_credito=cliente.saldo_credito)
            )

            # Commit para salvar todas as alterações
            await db.commit()

            # Refresh para garantir que os dados estão atualizados
            await db.refresh(cliente)

            logger.info(f"✅ Crédito adicionado: Cliente {cliente_id}, "
                        f"Valor: {valor_credito}, "
                        f"Novo saldo: {cliente.saldo_credito}")

            return cliente

        except ComandaValidationError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Erro ao adicionar crédito ao cliente {cliente_id}: {e}")
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
        ✅ VERSÃO COMPLETAMENTE SÍNCRONA - SEM GREENLET ERRORS
        """
        try:
            logger.info(f"🔄 Recalculando totais da comanda {comanda_id}")

            # ✅ BUSCAR APENAS A COMANDA BÁSICA PRIMEIRO
            result = await db.execute(select(Comanda).where(Comanda.id == comanda_id))
            comanda = result.scalar_one_or_none()

            if not comanda:
                logger.error(f"❌ Comanda {comanda_id} não encontrada para recálculo")
                return None

            # ✅ BUSCAR ITENS SEPARADAMENTE DE FORMA SIMPLES
            result_itens = await db.execute(
                select(ItemPedido.preco_unitario, ItemPedido.quantidade)
                .where(ItemPedido.id_comanda == comanda_id)
            )
            itens_data = result_itens.fetchall()

            # ✅ CALCULAR TOTAL DOS ITENS DE FORMA SÍNCRONA
            total_itens = Decimal("0.00")
            for preco_unitario, quantidade in itens_data:
                if preco_unitario and quantidade:
                    total_itens += Decimal(str(preco_unitario)) * Decimal(str(quantidade))

            # ✅ USAR VALORES DIRETOS DA COMANDA (SEM RELACIONAMENTOS)
            percentual_taxa = comanda.percentual_taxa_servico or Decimal("0.0")
            valor_taxa = (total_itens * percentual_taxa / Decimal("100")).quantize(Decimal("0.01"))
            desconto = comanda.valor_desconto or Decimal("0.0")
            valor_pago = comanda.valor_pago or Decimal("0.0")
            valor_credito = comanda.valor_credito_usado or Decimal("0.0")

            # ✅ CALCULAR VALORES FINAIS
            valor_total_original = max(Decimal("0.0"), total_itens + valor_taxa - desconto)
            valor_total_calculado = max(Decimal("0.0"), valor_total_original - valor_pago - valor_credito)

            logger.info(f"📊 Recálculo: Itens: {total_itens}, Taxa: {valor_taxa}, "
                        f"Desconto: {desconto}, Pago: {valor_pago}, "
                        f"Crédito: {valor_credito}, Saldo: {valor_total_calculado}")

            # ✅ ATUALIZAR USANDO UPDATE DIRETO (MAIS SEGURO)
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

            # ✅ COMMIT/FLUSH SEGURO
            if fazer_commit:
                await db.commit()
                logger.info(f"✅ Totais recalculados para comanda {comanda_id}")
            else:
                await db.flush()

            # ✅ BUSCAR COMANDA ATUALIZADA PARA RETORNO
            comanda_atualizada = await ComandaService.buscar_comanda_por_id(db, comanda_id)
            return comanda_atualizada

        except Exception as e:
            logger.error(f"❌ Erro ao recalcular totais da comanda {comanda_id}: {e}")
            if fazer_commit:
                try:
                    await db.rollback()
                except Exception as rollback_error:
                    logger.error(f"❌ Erro no rollback: {rollback_error}")
            return None


# Funções de compatibilidade
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


async def usar_credito_cliente_na_comanda(db: AsyncSession, comanda_id: int,
                                          valor_credito: Optional[Decimal] = None) -> Comanda:
    return await ComandaService.usar_credito_cliente(db, comanda_id, valor_credito)


async def adicionar_credito_ao_cliente(db: AsyncSession, cliente_id: int, valor_credito: Decimal,
                                       observacoes: Optional[str] = None) -> Cliente:
    return await ComandaService.adicionar_credito_cliente(db, cliente_id, valor_credito, observacoes)
