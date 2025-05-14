# app/routers/comanda_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.session import get_db_session
from app.schemas.comanda_schemas import ComandaCreate, ComandaUpdate, ComandaInResponse
from app.services.comanda_service import create_comanda, update_comanda, get_comanda_by_id, get_all_comandas

router = APIRouter(
    prefix="/comandas",
    tags=["Comandas"],
)

@router.post("/", response_model=ComandaInResponse)
def create_new_comanda(comanda: ComandaCreate, db: Session = Depends(get_db_session)):
    db_comanda = create_comanda(db=db, comanda=comanda)
    return db_comanda

@router.put("/{comanda_id}", response_model=ComandaInResponse)
def update_existing_comanda(comanda_id: str, comanda: ComandaUpdate, db: Session = Depends(get_db_session)):
    db_comanda = update_comanda(db=db, comanda_id=comanda_id, comanda=comanda)
    if not db_comanda:
        raise HTTPException(status_code=404, detail="Comanda not found")
    return db_comanda

@router.get("/{comanda_id}", response_model=ComandaInResponse)
def get_comanda(comanda_id: str, db: Session = Depends(get_db_session)):
    db_comanda = get_comanda_by_id(db=db, comanda_id=comanda_id)
    if not db_comanda:
        raise HTTPException(status_code=404, detail="Comanda not found")
    return db_comanda

@router.get("/", response_model=list[ComandaInResponse])
def get_comandas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    db_comandas = get_all_comandas(db=db, skip=skip, limit=limit)
    return db_comandas
