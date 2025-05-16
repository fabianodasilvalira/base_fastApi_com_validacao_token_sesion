from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.cliente import Cliente
from app.schemas.cliente_schemas import ClienteCreate, ClienteUpdate
from app.core.session import get_db_session


async def get_cliente(db_session: AsyncSession, cliente_id: int):  # Alterado cliente_id: str para cliente_id: int
    query = select(Cliente).where(Cliente.id == cliente_id)
    result = await db_session.execute(query)
    return result.scalars().first()


async def get_clientes(db_session: AsyncSession, skip: int = 0, limit: int = 10):
    query = select(Cliente).offset(skip).limit(limit)
    result = await db_session.execute(query)
    return result.scalars().all()


from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

async def create_cliente(db: AsyncSession, cliente_create: ClienteCreate):
    # Verifica se já existe cliente com MESMO nome e telefone
    query = select(Cliente).where(
        and_(
            Cliente.telefone == cliente_create.telefone,
            Cliente.nome == cliente_create.nome
        )
    )
    result = await db.execute(query)
    existing_cliente = result.scalars().first()

    if existing_cliente:
        raise HTTPException(status_code=400, detail="Telefone e nome já cadastrados")

    novo_cliente = Cliente(**cliente_create.dict())
    db.add(novo_cliente)
    try:
        await db.commit()
        await db.refresh(novo_cliente)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Erro ao criar cliente - possível duplicidade de dados")

    return novo_cliente



async def update_cliente(db_session: AsyncSession, cliente_id: int, cliente: ClienteUpdate):  # Alterado cliente_id: str para cliente_id: int
    db_cliente = await get_cliente(db_session, cliente_id)
    if db_cliente:
        for key, value in cliente.dict(exclude_unset=True).items():
            setattr(db_cliente, key, value)
        db_session.add(db_cliente)
        await db_session.commit()
        await db_session.refresh(db_cliente)
    return db_cliente


async def delete_cliente(db_session: AsyncSession, cliente_id: int):  # Alterado cliente_id: str para cliente_id: int
    db_cliente = await get_cliente(db_session, cliente_id)
    if db_cliente:
        await db_session.delete(db_cliente)
        await db_session.commit()
    return db_cliente

