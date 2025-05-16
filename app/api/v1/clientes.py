from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import get_db
from app.services.cliente_service import create_cliente, get_cliente, get_clientes, update_cliente, delete_cliente
from app.schemas.cliente_schemas import ClienteCreate, ClienteUpdate, ClienteOut

router = APIRouter()

@router.post("/", response_model=ClienteOut)
async def create(cliente: ClienteCreate, db_session: AsyncSession = Depends(get_db)):
    return await create_cliente(db_session, cliente)

@router.get("/{cliente_id}", response_model=ClienteOut)
async def read(cliente_id: int, db_session: AsyncSession = Depends(get_db)):  # cliente_id é int
    db_cliente = await get_cliente(db_session, cliente_id)
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return db_cliente

@router.get("/", response_model=list[ClienteOut])
async def read_multiple(skip: int = 0, limit: int = 10, db_session: AsyncSession = Depends(get_db)):
    return await get_clientes(db_session, skip, limit)

@router.put("/{cliente_id}", response_model=ClienteOut)
async def update(
    cliente_id: int,
    cliente: ClienteUpdate,
    db_session: AsyncSession = Depends(get_db)
):
    db_cliente = await update_cliente(db_session, cliente_id, cliente)
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return db_cliente

@router.delete("/{cliente_id}", response_model=ClienteOut)
async def delete(cliente_id: int, db_session: AsyncSession = Depends(get_db)):
    db_cliente = await delete_cliente(db_session, cliente_id)
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return db_cliente
