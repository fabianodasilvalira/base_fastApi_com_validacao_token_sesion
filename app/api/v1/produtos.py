from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.session import get_db_session
from app.schemas.produto_schemas import ProdutoCreate, ProdutoOut, ProdutoUpdate
from app.services import produto_service
from typing import List

router = APIRouter(prefix="/produtos", tags=["Produtos"])

@router.post("/", response_model=ProdutoOut)
def criar(produto: ProdutoCreate, db: Session = Depends(get_db_session())):
    return produto_service.criar_produto(db, produto)

@router.get("/", response_model=List[ProdutoOut])
def listar(db: Session = Depends(get_db_session)):
    return produto_service.listar_produtos(db)

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
