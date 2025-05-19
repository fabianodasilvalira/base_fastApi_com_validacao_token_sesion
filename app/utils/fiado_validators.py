from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Cliente, Comanda, User, Fiado


async def validate_fiado_create_data(db: AsyncSession, fiado_data):
    # Valida cliente
    result = await db.execute(select(Cliente).filter(Cliente.id == fiado_data.id_cliente))
    if not result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )

    # Valida comanda
    result = await db.execute(select(Comanda).filter(Comanda.id == fiado_data.id_comanda))
    if not result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comanda não encontrada"
        )

    # Valida valores monetários
    if fiado_data.valor_original <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valor original deve ser positivo"
        )

    if fiado_data.valor_devido and fiado_data.valor_devido > fiado_data.valor_original:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valor devido não pode ser maior que valor original"
        )


async def validate_pagamento_data(db: AsyncSession, pagamento_data):
    if pagamento_data.valor_pago <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valor do pagamento deve ser positivo"
        )