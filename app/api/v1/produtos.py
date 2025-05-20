from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api import deps
from app.core.session import get_db
from app.models import Produto, User
from app.schemas.produto_schemas import ProdutoCreate, ProdutoOut, ProdutoUpdate
from app.services import produto_service

router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.get("/", response_model=List[ProdutoOut])
async def listar(
    skip: int = Query(0, description="Número de registros para pular"),
    limit: int = Query(100, description="Limite de registros para retornar"),
    db: AsyncSession = Depends(get_db),
    usuario_atual: User = Depends(deps.get_current_user)

):
    return await produto_service.listar_produtos(db, skip=skip, limit=limit)


@router.get("/{produto_id}", response_model=ProdutoOut)
async def obter(produto_id: int, db: AsyncSession = Depends(get_db)):
    produto = await produto_service.obter_produto(db, produto_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto


@router.post("/", response_model=ProdutoOut)
async def criar(produto: ProdutoCreate, db: AsyncSession = Depends(get_db)):
    return await produto_service.criar_produto(db, produto)


@router.put("/{produto_id}", response_model=ProdutoOut)
async def atualizar(produto_id: int, produto: ProdutoUpdate, db: AsyncSession = Depends(get_db)):
    return await produto_service.atualizar_produto(db, produto_id, produto)


@router.delete("/{produto_id}", response_model=ProdutoOut)
async def deletar(produto_id: int, db: AsyncSession = Depends(get_db)):
    return await produto_service.deletar_produto(db, produto_id)


@router.get("/categoria/{categoria_id}", response_model=List[ProdutoOut])
async def listar_por_categoria(
    categoria_id: int,
    skip: int = Query(0, description="Número de registros para pular"),
    limit: int = Query(100, description="Limite de registros para retornar"),
    db: AsyncSession = Depends(get_db)
):
    return await produto_service.listar_produtos_por_categoria(db, categoria_id, skip=skip, limit=limit)
