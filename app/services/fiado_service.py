# app/services/fiado.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from app.models.fiado import Fiado
from app.schemas.fiado_schemas import FiadoCreate, FiadoUpdate, StatusFiado
from datetime import date


async def get_fiado_by_id(db: AsyncSession, fiado_id: int):
    """
    Busca um fiado pelo ID.
    """
    result = await db.execute(select(Fiado).filter(Fiado.id == fiado_id))
    return result.scalars().first()


async def create_fiado(db: AsyncSession, fiado_data: FiadoCreate):
    """
    Cria um novo registro de fiado.
    """
    db_fiado = Fiado(
        id_comanda=fiado_data.id_comanda,
        id_cliente=fiado_data.id_cliente,
        id_usuario_registrou=fiado_data.id_usuario_registrou,
        valor_original=fiado_data.valor_original,
        valor_devido=fiado_data.valor_devido,
        status_fiado=fiado_data.status_fiado,
        data_vencimento=fiado_data.data_vencimento,
        observacoes=fiado_data.observacoes,
    )
    db.add(db_fiado)
    await db.commit()
    await db.refresh(db_fiado)
    return db_fiado


async def update_fiado(db: AsyncSession, fiado_id: int, fiado_update_data: FiadoUpdate):
    """
    Atualiza as informações de um fiado existente.
    """
    db_fiado = await get_fiado_by_id(db, fiado_id)
    if db_fiado:
        # Atualiza os campos do fiado
        for key, value in fiado_update_data.dict(exclude_unset=True).items():
            setattr(db_fiado, key, value)

        await db.commit()
        await db.refresh(db_fiado)
    return db_fiado


async def get_fiados_by_cliente_id(db: AsyncSession, cliente_id: int):
    """
    Lista todos os fiados de um cliente específico.
    """
    result = await db.execute(select(Fiado).filter(Fiado.id_cliente == cliente_id))
    return result.scalars().all()


async def registrar_pagamento_em_fiado(
        db: AsyncSession,
        fiado_id: int,
        valor_pago: float,
        id_usuario_registrou: int = None,
        observacoes: str = None
):
    """
    Registra um pagamento (parcial ou total) em um fiado existente.
    """
    # Busca o fiado pelo ID
    db_fiado = await get_fiado_by_id(db, fiado_id)

    if not db_fiado:
        return None

    # Calcula o novo valor devido
    novo_valor_devido = max(0, db_fiado.valor_devido - valor_pago)

    # Determina o novo status com base no valor devido
    if novo_valor_devido == 0:
        novo_status = StatusFiado.PAGO_TOTALMENTE
    else:
        novo_status = StatusFiado.PAGO_PARCIALMENTE

    # Atualiza o fiado
    db_fiado.valor_devido = novo_valor_devido
    db_fiado.status_fiado = novo_status

    # Adiciona observações sobre o pagamento, se fornecidas
    if observacoes:
        nova_observacao = f"[{date.today()}] Pagamento de R${valor_pago:.2f}. {observacoes}"
        if db_fiado.observacoes:
            db_fiado.observacoes = f"{db_fiado.observacoes}\n{nova_observacao}"
        else:
            db_fiado.observacoes = nova_observacao

    # Registra o usuário que fez o pagamento, se fornecido
    if id_usuario_registrou:
        db_fiado.id_usuario_registrou = id_usuario_registrou

    await db.commit()
    await db.refresh(db_fiado)

    return db_fiado
