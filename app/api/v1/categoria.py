from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.session import get_db_session
from app.schemas.categoria_schemas import CategoriaResponse, CategoriaUpdate, CategoriaCreate
from app.services import categoria_service as service

router = APIRouter()

@router.get("/", response_model=List[CategoriaResponse])
def listar_categorias(db: Session = Depends(get_db_session)):
    return service.get_all(db)

@router.get("/{categoria_id}", response_model=CategoriaResponse)
def obter_categoria(categoria_id: int, db: Session = Depends(get_db_session)):
    categoria = service.get_by_id(db, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return categoria

@router.post("/", response_model=CategoriaResponse)
def criar_categoria(categoria: CategoriaCreate, db: Session = Depends(get_db_session)):
    return service.create(db, categoria)

@router.put("/{categoria_id}", response_model=CategoriaResponse)
def atualizar_categoria(categoria_id: int, categoria: CategoriaUpdate, db: Session = Depends(get_db_session)):
    categoria_atualizada = service.update(db, categoria_id, categoria)
    if not categoria_atualizada:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return categoria_atualizada

@router.delete("/{categoria_id}")
def deletar_categoria(categoria_id: int, db: Session = Depends(get_db_session)):
    sucesso = service.delete(db, categoria_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return {"ok": True}
