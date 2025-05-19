from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import get_db
from app.services.mesa_service import create_mesa, get_mesa, get_mesas, update_mesa, delete_mesa
from app.schemas.mesa_schemas import MesaCreate, MesaUpdate, MesaOut

router = APIRouter()

@router.post("/", response_model=MesaOut)
async def create(mesa: MesaCreate, db_session: AsyncSession = Depends(get_db)):
    """
    Cria uma nova mesa.

    - **mesa**: Dados da nova mesa a ser criada.
    - **return**: Objeto da mesa criada.
    """
    return await create_mesa(db_session, mesa)

@router.get("/{mesa_id}", response_model=MesaOut)
async def read(mesa_id: int, db_session: AsyncSession = Depends(get_db)):
    """
    Retorna os dados de uma mesa pelo ID.

    - **mesa_id**: ID da mesa que se deseja buscar.
    - **return**: Objeto da mesa encontrada.
    """
    db_mesa = await get_mesa(db_session, mesa_id)
    if not db_mesa:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    return db_mesa

@router.get("/", response_model=list[MesaOut])
async def read_multiple(skip: int = 0, limit: int = 100, db_session: AsyncSession = Depends(get_db)):
    """
    Lista todas as mesas cadastradas.

    - **skip**: Número de registros a pular (paginação).
    - **limit**: Número máximo de registros a retornar.
    - **return**: Lista de mesas.
    """
    return await get_mesas(db_session, skip, limit)

@router.put("/{mesa_id}", response_model=MesaOut)
async def update(
    mesa_id: int,
    mesa: MesaUpdate,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Atualiza os dados de uma mesa existente.

    - **mesa_id**: ID da mesa que será atualizada.
    - **mesa_update**: Dados atualizados da mesa.
    - **return**: Objeto da mesa atualizada.
    """
    db_mesa = await update_mesa(db_session, mesa_id, mesa)
    if not db_mesa:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    return db_mesa

@router.delete("/{mesa_id}", response_model=MesaOut)
async def delete(mesa_id: int, db_session: AsyncSession = Depends(get_db)):
    """
    Deleta uma mesa do sistema.

    - **mesa_id**: ID da mesa que será removida.
    - **return**: Objeto da mesa deletada.
    """
    db_mesa = await delete_mesa(db_session, mesa_id)
    if not db_mesa:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    return db_mesa
