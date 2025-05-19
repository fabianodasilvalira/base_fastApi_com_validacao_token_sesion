# app/services/mesa_service.py
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
import uuid

from app.models import Mesa
from app.models import Cliente
from app.schemas.mesa_schemas import MesaCreate, MesaUpdate


# Função para criar uma mesa
async def create_mesa(db_session: AsyncSession, mesa_create: MesaCreate):
    # Verifica se já existe uma mesa com o mesmo número identificador
    query = select(Mesa).where(Mesa.numero_identificador == mesa_create.numero_identificador)
    result = await db_session.execute(query)
    existing_mesa = result.scalars().first()

    if existing_mesa:
        raise HTTPException(status_code=400, detail="Mesa com este número identificador já existe")

    mesa_data = mesa_create.dict(exclude_unset=True)

    # Verifica se o cliente associado existe, caso tenha sido fornecido
    if mesa_data.get('id_cliente_associado'):
        cliente_query = select(Cliente).where(Cliente.id == mesa_data['id_cliente_associado'])
        cliente_result = await db_session.execute(cliente_query)
        cliente = cliente_result.scalars().first()

        if not cliente:
            raise HTTPException(
                status_code=400,
                detail=f"Cliente com ID {mesa_data['id_cliente_associado']} não encontrado"
            )

    # Gera um QR code hash se não foi fornecido
    if not mesa_data.get('qr_code_hash'):
        mesa_data['qr_code_hash'] = str(uuid.uuid4())

    try:
        db_mesa = Mesa(**mesa_data)
        db_session.add(db_mesa)
        await db_session.commit()
        await db_session.refresh(db_mesa)
        return db_mesa
    except IntegrityError as e:
        await db_session.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Erro de integridade ao criar mesa: {str(e)}"
        )
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar mesa: {str(e)}"
        )


# Função para obter uma mesa pelo ID
async def get_mesa(db_session: AsyncSession, mesa_id: int):
    query = select(Mesa).where(Mesa.id == mesa_id)
    result = await db_session.execute(query)
    return result.scalars().first()


# Função para obter todas as mesas
async def get_mesas(db_session: AsyncSession, skip: int = 0, limit: int = 100):
    query = select(Mesa).offset(skip).limit(limit)
    result = await db_session.execute(query)
    return result.scalars().all()


# Função para atualizar os dados de uma mesa
async def update_mesa(db_session: AsyncSession, mesa_id: int, mesa_update: MesaUpdate):
    db_mesa = await get_mesa(db_session, mesa_id)
    if not db_mesa:
        return None

    # Atualizando apenas os campos fornecidos
    update_data = mesa_update.dict(exclude_unset=True)

    # Verifica se o cliente associado existe, caso tenha sido fornecido
    if 'id_cliente_associado' in update_data and update_data['id_cliente_associado'] is not None:
        cliente_query = select(Cliente).where(Cliente.id == update_data['id_cliente_associado'])
        cliente_result = await db_session.execute(cliente_query)
        cliente = cliente_result.scalars().first()

        if not cliente:
            raise HTTPException(
                status_code=400,
                detail=f"Cliente com ID {update_data['id_cliente_associado']} não encontrado"
            )

    try:
        for key, value in update_data.items():
            setattr(db_mesa, key, value)

        db_session.add(db_mesa)
        await db_session.commit()
        await db_session.refresh(db_mesa)
        return db_mesa
    except IntegrityError as e:
        await db_session.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Erro de integridade ao atualizar mesa: {str(e)}"
        )
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar mesa: {str(e)}"
        )


# Função para deletar uma mesa
async def delete_mesa(db_session: AsyncSession, mesa_id: int):
    db_mesa = await get_mesa(db_session, mesa_id)
    if db_mesa:
        try:
            await db_session.delete(db_mesa)
            await db_session.commit()
            return db_mesa
        except IntegrityError as e:
            await db_session.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Não é possível excluir esta mesa pois ela possui registros associados: {str(e)}"
            )
        except Exception as e:
            await db_session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao excluir mesa: {str(e)}"
            )
    return None
