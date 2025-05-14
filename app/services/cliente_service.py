from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.cliente import Cliente
from app.schemas.cliente_schemas import ClienteCreate, ClienteUpdate
from app.core.session import get_db_session


async def get_cliente(db_session: AsyncSession, cliente_id: str):
    query = select(Cliente).where(Cliente.id == cliente_id)
    result = await db_session.execute(query)
    return result.scalars().first()


async def get_clientes(db_session: AsyncSession, skip: int = 0, limit: int = 10):
    query = select(Cliente).offset(skip).limit(limit)
    result = await db_session.execute(query)
    return result.scalars().all()


async def create_cliente(db_session: AsyncSession, cliente: ClienteCreate):
    db_cliente = Cliente(
        nome=cliente.nome,
        telefone=cliente.telefone,
        observacoes=cliente.observacoes,
        endereco=cliente.endereco,
    )
    db_session.add(db_cliente)
    await db_session.commit()
    await db_session.refresh(db_cliente)
    return db_cliente


async def update_cliente(db_session: AsyncSession, cliente_id: str, cliente: ClienteUpdate):
    db_cliente = await get_cliente(db_session, cliente_id)
    if db_cliente:
        for key, value in cliente.dict(exclude_unset=True).items():
            setattr(db_cliente, key, value)
        db_session.add(db_cliente)
        await db_session.commit()
        await db_session.refresh(db_cliente)
    return db_cliente


async def delete_cliente(db_session: AsyncSession, cliente_id: str):
    db_cliente = await get_cliente(db_session, cliente_id)
    if db_cliente:
        await db_session.delete(db_cliente)
        await db_session.commit()
    return db_cliente
