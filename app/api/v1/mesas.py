# app/routers/mesa.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.session import get_db_session
from app.services.mesa_service import create_mesa, get_mesa, get_mesas, update_mesa, delete_mesa
from app.schemas.mesa_schemas import MesaCreate, MesaOut, MesaUpdate

router = APIRouter()

# Endpoint para criar uma mesa
@router.post("/", response_model=MesaOut)
def create_new_mesa(mesa: MesaCreate, db: Session = Depends(get_db_session)):
    return create_mesa(db=db, mesa=mesa)

# Endpoint para obter uma mesa pelo ID
@router.get("/{mesa_id}", response_model=MesaOut)
def read_mesa(mesa_id: int, db: Session = Depends(get_db_session)):
    db_mesa = get_mesa(db=db, mesa_id=mesa_id)
    if db_mesa is None:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    return db_mesa

# Endpoint para obter todas as mesas
@router.get("/", response_model=list[MesaOut])
def read_mesas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    return get_mesas(db=db, skip=skip, limit=limit)

# Endpoint para atualizar os dados de uma mesa
@router.put("/{mesa_id}", response_model=MesaOut)
def update_mesa_data(mesa_id: int, mesa_update: MesaUpdate, db: Session = Depends(get_db_session)):
    db_mesa = update_mesa(db=db, mesa_id=mesa_id, mesa_update=mesa_update)
    if db_mesa is None:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    return db_mesa

# Endpoint para deletar uma mesa
@router.delete("/{mesa_id}", response_model=MesaOut)
def delete_mesa_data(mesa_id: int, db: Session = Depends(get_db_session)):
    db_mesa = delete_mesa(db=db, mesa_id=mesa_id)
    if db_mesa is None:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    return db_mesa
