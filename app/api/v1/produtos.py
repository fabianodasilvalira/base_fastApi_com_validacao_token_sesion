from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.session import get_db
from app.models import User
from app.schemas.produto_schemas import ProdutoCreate, ProdutoOut, ProdutoUpdate, CategoriaComProdutosOut
from app.services import produto_service
from app.api import deps

router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.get("/", response_model=List[ProdutoOut])
async def listar_produtos(
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros para retornar"),
    db: AsyncSession = Depends(get_db),
    # usuario_atual: User = Depends(deps.get_current_user)
):
    """Lista todos os produtos com paginação."""
    return await produto_service.listar_produtos(db, skip=skip, limit=limit)


@router.get("/cardapio", response_model=List[CategoriaComProdutosOut])
async def listar_cardapio(
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros para retornar"),
    db: AsyncSession = Depends(get_db),
):
    """Lista produtos agrupados por categoria para cardápio."""
    return await produto_service.listar_cardapio(db, skip=skip, limit=limit)


@router.get("/categoria/{categoria_id}", response_model=List[ProdutoOut])
async def listar_por_categoria(
    categoria_id: int,
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros para retornar"),
    db: AsyncSession = Depends(get_db)
):
    """Lista produtos de uma categoria específica."""
    return await produto_service.listar_produtos_por_categoria(db, categoria_id, skip=skip, limit=limit)


@router.get("/{produto_id}", response_model=ProdutoOut)
async def obter_produto(
    produto_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Obtém um produto específico por ID."""
    produto = await produto_service.obter_produto(db, produto_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto


@router.post("/", response_model=ProdutoOut)
async def criar_produto(
    produto: ProdutoCreate,
    db: AsyncSession = Depends(get_db),
    # usuario_atual: User = Depends(deps.get_current_user)
):
    """Cria um novo produto."""
    return await produto_service.criar_produto(db, produto)


@router.put("/{produto_id}", response_model=ProdutoOut)
async def atualizar_produto(
    produto_id: int,
    produto: ProdutoUpdate,
    db: AsyncSession = Depends(get_db),
    # usuario_atual: User = Depends(deps.get_current_user)
):
    """Atualiza um produto existente."""
    return await produto_service.atualizar_produto(db, produto_id, produto)


@router.delete("/{produto_id}", response_model=ProdutoOut)
async def deletar_produto(
    produto_id: int,
    db: AsyncSession = Depends(get_db),
    # usuario_atual: User = Depends(deps.get_current_user)
):
    """Deleta um produto."""
    return await produto_service.deletar_produto(db, produto_id)


@router.post("/resetar-sequencia")
async def resetar_sequencia(
    db: AsyncSession = Depends(get_db),
    # usuario_atual: User = Depends(deps.get_current_user)
):
    """Endpoint utilitário para resetar a sequência de IDs (use com cuidado)."""
    return await produto_service.resetar_sequencia_produtos(db)
