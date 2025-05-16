from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.session import get_db_session
from app.schemas.categoria_schemas import CategoriaResponse, CategoriaUpdate, CategoriaCreate
from app.services import categoria_service as service

router = APIRouter()

@router.get("/", response_model=List[CategoriaResponse])
async def listar_categorias(db: AsyncSession = Depends(get_db_session)):
    async with db as session:
        return await service.get_all(session)

@router.get("/{categoria_id}", response_model=CategoriaResponse)
async def obter_categoria(categoria_id: int, db: AsyncSession = Depends(get_db_session)):
    async with db as session:
        categoria = await service.get_by_id(session, categoria_id)
        if not categoria:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        return categoria

@router.post("/", response_model=CategoriaResponse, status_code=201)
async def criar_categoria(categoria: CategoriaCreate, db: AsyncSession = Depends(get_db_session)):
    async with db as session:
        return await service.create(session, categoria)

@router.put("/{categoria_id}", response_model=CategoriaResponse)
async def atualizar_categoria(
    categoria_id: int,
    categoria: CategoriaUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    async with db as session:
        categoria_atualizada = await service.update(session, categoria_id, categoria)
        if not categoria_atualizada:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        return categoria_atualizada

@router.delete("/{categoria_id}", status_code=204)
async def deletar_categoria(categoria_id: int, db: AsyncSession = Depends(get_db_session)):
    async with db as session:
        sucesso = await service.delete(session, categoria_id)
        if not sucesso:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")