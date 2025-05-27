import logging
import uuid
from sqlalchemy import select, or_, update
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from typing import List, Optional
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
logging.basicConfig(level=logging.INFO)


async def create_comanda(db: AsyncSession, comanda_data: ComandaCreate) -> Comanda:
    """Cria uma nova comanda no banco de dados."""
    qr_code = comanda_data.qr_code_comanda_hash or str(uuid.uuid4())

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

    # Recarregar com relacionamentos para retorno completo
    result = await db.execute(
        select(Comanda)
        .options(
            selectinload(Comanda.itens_pedido),
            selectinload(Comanda.pagamentos),
            selectinload(Comanda.fiados_registrados),
            joinedload(Comanda.mesa),
            joinedload(Comanda.cliente),
        )
        .where(Comanda.id == db_comanda.id)
    )
    comanda_completa = result.scalar_one()
    return comanda_completa


async def get_comanda_by_id(db: AsyncSession, comanda_id: int) -> Optional[Comanda]:
    """Busca uma comanda pelo seu ID, carregando relacionamentos para evitar erro de serialização."""
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


async def get_comanda_by_id_detail(db: AsyncSession, comanda_id: int) -> Optional[Comanda]:
    try:
        logger.debug(f"📦 Executando query para comanda_id={comanda_id}")
        result = await db.execute(
            select(Comanda)
            .options(
                joinedload(Comanda.mesa),
                joinedload(Comanda.cliente),
                joinedload(Comanda.itens_pedido),
                joinedload(Comanda.pagamentos),
                joinedload(Comanda.fiados_registrados),
            )
            .where(Comanda.id == comanda_id)
        )
        row = result.unique().one_or_none()
        if row:
            return row[0]
        return None
    except Exception as e:
        logger.exception(f"❌ Erro ao buscar comanda: {e}")
        return None


async def get_all_comandas_detailed(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Comanda]:
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
    )
    return result.scalars().all()


async def get_active_comanda_by_mesa_id(db: AsyncSession, mesa_id: int):
    query = (
        select(Comanda)
        .options(
            joinedload(Comanda.mesa),
        )
        .where(
            Comanda.id_mesa == mesa_id,
            Comanda.status_comanda == StatusComanda.ABERTA,
        )
        .order_by(Comanda.id.desc())
    )

    result = await db.execute(query)
    comanda = result.scalars().first()

    if comanda:
        await db.refresh(comanda, attribute_names=["itens_pedido", "pagamentos", "fiados_registrados"])
    return comanda


async def registrar_pagamento_na_comanda(db: AsyncSession, comanda_id: int,
                                         pagamento_data: PagamentoCreateSchema) -> Comanda:
    """Registra um pagamento na comanda, atualiza valores pagos e status."""
    comanda = await get_comanda_by_id(db, comanda_id)
    if not comanda:
        raise ValueError(f"Comanda com id {comanda_id} não encontrada para registrar pagamento.")

    novo_pagamento = Pagamento(
        id_comanda=comanda_id,
        id_cliente=pagamento_data.id_cliente,
        id_usuario_registrou=pagamento_data.id_usuario_registrou,
        valor_pago=pagamento_data.valor_pago,
        metodo_pagamento=pagamento_data.metodo_pagamento,
        observacoes=pagamento_data.observacoes
    )
    db.add(novo_pagamento)

    # Atualiza o valor pago acumulado
    comanda.valor_pago = (comanda.valor_pago or Decimal(0)) + pagamento_data.valor_pago

    # MODIFICAÇÃO: Recalcula o valor_total_calculado (saldo devedor restante)
    comanda.atualizar_valores_comanda()

    # Atualiza o status baseado no saldo devedor restante (valor_total_calculado)
    if comanda.valor_total_calculado <= Decimal(0):
        comanda.status_comanda = StatusComanda.PAGA_TOTALMENTE
    elif comanda.valor_pago > 0 or comanda.valor_fiado > 0 or comanda.valor_credito_usado > 0:
        comanda.status_comanda = StatusComanda.PAGA_PARCIALMENTE

    await db.commit()
    await db.refresh(comanda)
    return comanda


async def registrar_saldo_como_fiado(db: AsyncSession, comanda_id: int, fiado_data: FiadoCreate) -> Comanda:
    """Registra o saldo devedor da comanda como fiado."""
    comanda = await get_comanda_by_id(db, comanda_id)
    if not comanda:
        raise ValueError(f"Comanda com id {comanda_id} não encontrada para registrar fiado.")

    novo_fiado = Fiado(
        id_comanda=comanda_id,
        id_cliente=fiado_data.id_cliente,
        valor_original=fiado_data.valor_original,
        valor_devido=fiado_data.valor_devido,
        observacoes=fiado_data.observacoes
    )
    db.add(novo_fiado)

    comanda.valor_fiado = (comanda.valor_fiado or Decimal(0)) + fiado_data.valor_devido

    # MODIFICAÇÃO: Recalcula o valor_total_calculado (saldo devedor restante)
    comanda.atualizar_valores_comanda()

    comanda.status_comanda = StatusComanda.EM_FIADO

    await db.commit()
    await db.refresh(comanda)
    return comanda


async def fechar_comanda(db: AsyncSession, comanda_id: int) -> Optional[Comanda]:
    """
    Fecha a comanda, que só pode ser fechada se estiver totalmente paga ou com saldo em fiado.
    """
    comanda = await get_comanda_by_id(db, comanda_id)
    if not comanda:
        return None

    if comanda.status_comanda not in [StatusComanda.PAGA_TOTALMENTE, StatusComanda.EM_FIADO]:
        return None

    comanda.status_comanda = StatusComanda.FECHADA
    await db.commit()
    await db.refresh(comanda)
    return comanda


async def gerar_ou_obter_qrcode_comanda(db: AsyncSession, comanda_id: int) -> Optional[Comanda]:
    """
    Gera um QRCode único para a comanda, ou retorna o existente.
    """
    comanda = await get_comanda_by_id(db, comanda_id)
    if not comanda:
        return None

    if not comanda.qr_code_comanda_hash:
        comanda.qr_code_comanda_hash = str(uuid.uuid4())
        await db.commit()
        await db.refresh(comanda)

    return comanda


# Funções auxiliares para buscar Cliente e Mesa
async def buscar_cliente(db: AsyncSession, cliente_id: int):
    result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    return result.scalar_one_or_none()


async def buscar_mesa(db: AsyncSession, mesa_id: int):
    result = await db.execute(select(Mesa).where(Mesa.id == mesa_id))
    return result.scalar_one_or_none()


async def recalculate_comanda_totals(db: AsyncSession, id_comanda: int, fazer_commit: bool = True) -> Optional[Comanda]:
    """
    MODIFICAÇÃO: Recalcula os valores onde valor_total_calculado representa o saldo devedor restante:
    - valor_final_comanda = apenas total dos itens
    - valor_total_calculado = (total dos itens + taxa - desconto) - (valor_pago + valor_fiado + valor_credito_usado)
    """
    try:
        logger.info(f"🔄 Iniciando recálculo da comanda {id_comanda}")

        # 1. Calcular total dos itens usando agregação SQL direta
        result_totais = await db.execute(
            select(
                func.coalesce(func.sum(ItemPedido.preco_unitario * ItemPedido.quantidade), 0).label('total_itens')
            ).where(ItemPedido.id_comanda == id_comanda)
        )
        total_itens = Decimal(str(result_totais.scalar() or 0))

        # 2. Buscar dados da comanda para calcular taxa, desconto e valores pagos
        result_comanda = await db.execute(
            select(
                Comanda.percentual_taxa_servico,
                Comanda.valor_desconto,
                Comanda.valor_pago,
                Comanda.valor_fiado,
                Comanda.valor_credito_usado
            ).where(Comanda.id == id_comanda)
        )
        comanda_data = result_comanda.first()

        if not comanda_data:
            logger.error(f"❌ Comanda {id_comanda} não encontrada")
            return None

        # 3. Calcular valores conforme nova lógica
        percentual_taxa = comanda_data.percentual_taxa_servico or Decimal("0.0")
        valor_taxa = (total_itens * percentual_taxa / Decimal("100")).quantize(Decimal("0.01"))
        desconto = comanda_data.valor_desconto or Decimal("0.0")

        # Calcular valor total original (antes dos pagamentos)
        valor_total_original = max(Decimal("0.0"), total_itens + valor_taxa - desconto)

        # MODIFICAÇÃO: valor_total_calculado agora é o saldo devedor restante
        valor_pago = comanda_data.valor_pago or Decimal("0.0")
        valor_fiado = comanda_data.valor_fiado or Decimal("0.0")
        valor_credito = comanda_data.valor_credito_usado or Decimal("0.0")

        valor_final_comanda = total_itens  # apenas total dos itens
        valor_total_calculado = max(Decimal("0.0"), valor_total_original - valor_pago - valor_fiado - valor_credito)

        # 4. UPDATE DIRETO no banco - GARANTIA DE PERSISTÊNCIA
        await db.execute(
            update(Comanda)
            .where(Comanda.id == id_comanda)
            .values(
                valor_final_comanda=valor_final_comanda,  # apenas total dos itens
                valor_taxa_servico=valor_taxa,
                valor_total_calculado=valor_total_calculado,  # saldo devedor restante
                updated_at=datetime.now()
            )
        )

        # 5. Commit ou flush conforme solicitado
        if fazer_commit:
            await db.commit()
            logger.info(
                f"✅ Comanda {id_comanda} recalculada e COMMITADA: Total Itens={total_itens}, Taxa={valor_taxa}, Saldo Devedor={valor_total_calculado}")
        else:
            await db.flush()
            logger.info(
                f"🔄 Comanda {id_comanda} recalculada (FLUSH): Total Itens={total_itens}, Taxa={valor_taxa}, Saldo Devedor={valor_total_calculado}")

        # 6. Retornar comanda atualizada
        result_updated = await db.execute(
            select(Comanda).where(Comanda.id == id_comanda)
        )
        comanda_atualizada = result_updated.scalar_one_or_none()

        logger.info(
            f"🎯 Recálculo concluído - Comanda {id_comanda} | Total Itens: {comanda_atualizada.valor_final_comanda if comanda_atualizada else 'N/A'} | Saldo Devedor: {comanda_atualizada.valor_total_calculado if comanda_atualizada else 'N/A'}")
        return comanda_atualizada

    except Exception as e:
        logger.exception(f"💥 ERRO CRÍTICO ao recalcular comanda {id_comanda}: {e}")
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
