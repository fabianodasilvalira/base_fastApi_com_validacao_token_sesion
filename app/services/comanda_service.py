# app/services/comanda_service.py
import logging


import uuid
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from typing import List, Optional
from decimal import Decimal

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
                joinedload(Comanda.fiados_registrados),  # <- ADICIONE ESTA LINHA
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
            selectinload(Comanda.itens_pedido),  # <-- carrega itens_pedido
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
            # Cuidado com collections! Pode dar problema, se quiser, carregue manualmente depois
            # joinedload(Comanda.itens_pedido),
            # joinedload(Comanda.pagamentos),
            # joinedload(Comanda.fiados_registrados),
        )
        .where(
            Comanda.id_mesa == mesa_id,
            Comanda.status_comanda == StatusComanda.ABERTA,
        )
        .order_by(Comanda.id.desc())  # opcional: pegar a comanda mais recente
    )

    result = await db.execute(query)
    comanda = result.scalars().first()  # Pega o primeiro resultado ou None

    # Se quiser carregar coleções separadamente (exemplo de carregamento preguiçoso)
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

    # Atualiza o status da comanda
    if comanda.valor_pago >= (comanda.valor_total_calculado or Decimal(0)):
        comanda.status_comanda = StatusComanda.PAGA_TOTALMENTE
    elif comanda.valor_pago > 0:
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


async def recalculate_comanda_totals(db: AsyncSession, id_comanda: int) -> float:
    try:
        # Buscar todos os pedidos da comanda
        result_pedidos = await db.execute(
            select(Pedido).where(Pedido.id_comanda == id_comanda)
        )
        pedidos = result_pedidos.scalars().all()

        total_comanda = 0.0

        for pedido in pedidos:
            # Buscar itens do pedido
            result_itens = await db.execute(
                select(ItemPedido).where(ItemPedido.id_pedido == pedido.id)
            )
            itens = result_itens.scalars().all()

            # Somar total dos itens do pedido
            total_pedido = sum(item.preco_unitario * item.quantidade for item in itens)
            total_comanda += total_pedido

        return total_comanda

    except Exception as e:
        logger.exception(f"Erro ao calcular total da comanda {id_comanda}: {e}")
        return 0.0
