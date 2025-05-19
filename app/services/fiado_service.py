# app/services/fiado_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from app.models import Cliente, Comanda
from app.models.fiado import Fiado
from app.models.user import User
from app.schemas.fiado_schemas import FiadoCreate, FiadoUpdate, StatusFiado
from datetime import date
from fastapi import HTTPException, status


async def verificar_usuario_existe(db: AsyncSession, usuario_id: int):
    if usuario_id is None:
        return True
    result = await db.execute(select(User).filter(User.id == usuario_id))
    usuario = result.scalars().first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário com ID {usuario_id} não encontrado"
        )
    return True


async def verificar_cliente_existe(db: AsyncSession, cliente_id: int):
    result = await db.execute(select(Cliente).filter(Cliente.id == cliente_id))
    cliente = result.scalars().first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente com ID {cliente_id} não encontrado"
        )
    return True


async def verificar_comanda_existe(db: AsyncSession, comanda_id: int):
    result = await db.execute(select(Comanda).filter(Comanda.id == comanda_id))
    comanda = result.scalars().first()
    if not comanda:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comanda com ID {comanda_id} não encontrada"
        )
    return True


async def validar_valores(valor_original: float, valor_devido: float = None):
    """
    Valida os valores monetários do fiado.
    """
    if valor_original <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O valor original deve ser maior que zero"
        )

    if valor_devido is not None and valor_devido < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O valor devido não pode ser negativo"
        )

    if valor_devido is not None and valor_devido > valor_original:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O valor devido não pode ser maior que o valor original"
        )

    return True


async def get_fiado_by_id(db: AsyncSession, fiado_id: int):
    result = await db.execute(select(Fiado).filter(Fiado.id == fiado_id))
    fiado = result.scalars().first()
    if not fiado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fiado com ID {fiado_id} não encontrado"
        )
    return fiado


async def create_fiado(db: AsyncSession, fiado_data: FiadoCreate):
    # Verifica se cliente existe
    await verificar_cliente_existe(db, fiado_data.id_cliente)

    # Verifica se comanda existe
    await verificar_comanda_existe(db, fiado_data.id_comanda)

    # Verifica se usuário registrador existe
    await verificar_usuario_existe(db, fiado_data.id_usuario_registrou)

    # Valida os valores monetários
    await validar_valores(fiado_data.valor_original, fiado_data.valor_devido)

    # Cria novo fiado
    novo_fiado = Fiado(
        id_comanda=fiado_data.id_comanda,
        id_cliente=fiado_data.id_cliente,
        id_usuario_registrou=fiado_data.id_usuario_registrou,
        valor_original=fiado_data.valor_original,
        valor_devido=fiado_data.valor_devido,
        status_fiado=fiado_data.status_fiado,
        data_vencimento=fiado_data.data_vencimento,
        observacoes=fiado_data.observacoes
    )

    db.add(novo_fiado)
    await db.commit()
    await db.refresh(novo_fiado)

    return novo_fiado


async def update_fiado(db: AsyncSession, fiado_id: int, fiado_update_data: FiadoUpdate):
    # Busca o fiado existente
    fiado = await get_fiado_by_id(db, fiado_id)

    # Extrai apenas os campos que foram fornecidos para atualização
    update_data = fiado_update_data.dict(exclude_unset=True)

    # Verifica entidades relacionadas se foram fornecidas
    if 'id_cliente' in update_data:
        await verificar_cliente_existe(db, update_data['id_cliente'])

    if 'id_comanda' in update_data:
        await verificar_comanda_existe(db, update_data['id_comanda'])

    if 'id_usuario_registrou' in update_data:
        await verificar_usuario_existe(db, update_data['id_usuario_registrou'])

    # Valida valores monetários se foram fornecidos
    valor_original = update_data.get('valor_original', fiado.valor_original)
    valor_devido = update_data.get('valor_devido', fiado.valor_devido)

    await validar_valores(valor_original, valor_devido)

    # Atualiza os campos do fiado
    for attr, value in update_data.items():
        setattr(fiado, attr, value)

    # Atualiza o status do fiado com base no valor devido
    if valor_devido == 0:
        fiado.status_fiado = StatusFiado.PAGO_TOTALMENTE
    elif valor_devido < fiado.valor_original:
        fiado.status_fiado = StatusFiado.PAGO_PARCIALMENTE

    await db.commit()
    await db.refresh(fiado)

    return fiado


async def get_fiados_by_cliente_id(db: AsyncSession, cliente_id: int, skip: int = 0, limit: int = 100):
    # Verifica se o cliente existe
    await verificar_cliente_existe(db, cliente_id)

    # Busca os fiados com paginação
    result = await db.execute(
        select(Fiado)
        .filter(Fiado.id_cliente == cliente_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def registrar_pagamento_em_fiado(db: AsyncSession, fiado_id: int, valor_pago: float, id_usuario_registrou: int,
                                       observacoes: str = None):
    # Verifica se o valor pago é válido
    if valor_pago <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O valor do pagamento deve ser maior que zero"
        )

    # Busca o fiado
    fiado = await get_fiado_by_id(db, fiado_id)

    # Verifica se o usuário existe
    await verificar_usuario_existe(db, id_usuario_registrou)

    # Verifica se o fiado já está totalmente pago
    if fiado.status_fiado == StatusFiado.PAGO_TOTALMENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este fiado já está totalmente pago"
        )

    # Verifica se o valor pago é maior que o valor devido
    if valor_pago > fiado.valor_devido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"O valor do pagamento (R${valor_pago:.2f}) não pode ser maior que o valor devido (R${fiado.valor_devido:.2f})"
        )

    # Atualiza o valor devido
    fiado.valor_devido = max(fiado.valor_devido - valor_pago, 0)

    # Atualiza o status do fiado
    if fiado.valor_devido == 0:
        fiado.status_fiado = StatusFiado.PAGO_TOTALMENTE
    else:
        fiado.status_fiado = StatusFiado.PAGO_PARCIALMENTE

    # Adiciona observação sobre o pagamento
    data_atual = date.today().strftime("%d/%m/%Y")
    nova_observacao = f"\nPagamento de R${valor_pago:.2f} registrado em {data_atual}"
    if observacoes:
        nova_observacao += f": {observacoes}"

    fiado.observacoes = (fiado.observacoes or '') + nova_observacao

    await db.commit()
    await db.refresh(fiado)
    return fiado
