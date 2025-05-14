# app/services/mesa.py
from sqlalchemy.orm import Session
from app.models.mesa import Mesa
from app.schemas.mesa_schemas import MesaCreate, MesaUpdate

# Função para criar uma mesa
def create_mesa(db: Session, mesa: MesaCreate):
    db_mesa = Mesa(**mesa.dict())
    db.add(db_mesa)
    db.commit()
    db.refresh(db_mesa)
    return db_mesa

# Função para obter uma mesa pelo ID
def get_mesa(db: Session, mesa_id: int):
    return db.query(Mesa).filter(Mesa.id == mesa_id).first()

# Função para obter todas as mesas
def get_mesas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Mesa).offset(skip).limit(limit).all()

# Função para atualizar os dados de uma mesa
def update_mesa(db: Session, mesa_id: int, mesa_update: MesaUpdate):
    db_mesa = db.query(Mesa).filter(Mesa.id == mesa_id).first()
    if db_mesa:
        for key, value in mesa_update.dict(exclude_unset=True).items():
            setattr(db_mesa, key, value)
        db.commit()
        db.refresh(db_mesa)
    return db_mesa

# Função para deletar uma mesa
def delete_mesa(db: Session, mesa_id: int):
    db_mesa = db.query(Mesa).filter(Mesa.id == mesa_id).first()
    if db_mesa:
        db.delete(db_mesa)
