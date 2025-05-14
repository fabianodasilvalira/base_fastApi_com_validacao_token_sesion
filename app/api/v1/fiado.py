# app/api/v1/fiado.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.session import get_db_session
from app.services.fiado_service import create_fiado, get_fiado, update_fiado
from app.schemas.fiado_schemas import FiadoCreate, FiadoUpdate, Fiado

router = APIRouter()

@router.post("/", response_model=Fiado)
def create_fiado_view(fiado: FiadoCreate, db: Session = Depends(get_db_session())):
    return create_fiado(db=db, fiado=fiado)

@router.get("/{fiado_id}", response_model=Fiado)
def read_fiado(fiado_id: int, db: Session = Depends(get_db_session)):
    db_fiado = get_fiado(db, fiado_id=fiado_id)
    if db_fiado is None:
        raise HTTPException(status_code=404, detail="Fiado not found")
    return db_fiado

@router.put("/{fiado_id}", response_model=Fiado)
def update_fiado_view(fiado_id: int, fiado: FiadoUpdate, db: Session = Depends(get_db_session)):
    db_fiado = update_fiado(db, fiado_id=fiado_id, fiado=fiado)
    if db_fiado is None:
        raise HTTPException(status_code=404, detail="Fiado not found")
    return db_fiado
