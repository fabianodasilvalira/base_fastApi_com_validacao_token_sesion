from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.session import get_db_session
from app.schemas.produto_schemas import ProdutoCreate, ProdutoOut, ProdutoUpdate
from app.services import produto_service
from typing import List

router = APIRouter(prefix="/produtos", tags=["Produtos"])

@router.post("/", response_model=ProdutoOut)
def criar(produto: ProdutoCreate, db: Session = Depends(get_db_session)):
    return produto_service.criar_produto(db, produto)

@router.get("/", response_model=List[ProdutoOut])
def listar(
    skip: int = Query(0, description="Número de registros para pular"),
    limit: int = Query(100, description="Limite de registros para retornar"),
    db: Session = Depends(get_db_session)
):
    return produto_service.listar_produtos(db, skip=skip, limit=limit)

@router.get("/{produto_id}", response_model=ProdutoOut)
def obter(produto_id: int, db: Session = Depends(get_db_session)):
    produto = produto_service.obter_produto(db, produto_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

@router.put("/{produto_id}", response_model=ProdutoOut)
def atualizar(produto_id: int, produto: ProdutoUpdate, db: Session = Depends(get_db_session)):
    return produto_service.atualizar_produto(db, produto_id, produto)

@router.delete("/{produto_id}", response_model=ProdutoOut)
def deletar(produto_id: int, db: Session = Depends(get_db_session)):
    return produto_service.deletar_produto(db, produto_id)

@router.get("/categoria/{categoria_id}", response_model=List[ProdutoOut])
def listar_por_categoria(
    categoria_id: int,
    skip: int = Query(0, description="Número de registros para pular"),
    limit: int = Query(100, description="Limite de registros para retornar"),
    db: Session = Depends(get_db_session)
):
    return produto_service.listar_produtos_por_categoria(db, categoria_id, skip=skip, limit=limit)
