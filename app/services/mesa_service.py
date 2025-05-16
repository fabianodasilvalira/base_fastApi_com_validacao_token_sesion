# app/services/mesa.py
from sqlalchemy.orm import Session
from app.models.mesa import Mesa
from app.schemas.mesa_schemas import MesaCreate, MesaUpdate
import uuid


# Função para criar uma mesa
def create_mesa(db: Session, mesa: MesaCreate):
    # Convertendo o modelo Pydantic para dicionário e excluindo None values
    mesa_data = mesa.dict(exclude_unset=True)

    # Gerando QR code hash se não foi fornecido
    if not mesa_data.get('qr_code_hash'):
        mesa_data['qr_code_hash'] = str(uuid.uuid4())

    db_mesa = Mesa(**mesa_data)
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
        # Atualizando apenas os campos fornecidos
        update_data = mesa_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_mesa, key, value)
        db.commit()
        db.refresh(db_mesa)
    return db_mesa


# Função para deletar uma mesa
def delete_mesa(db: Session, mesa_id: int):
    db_mesa = db.query(Mesa).filter(Mesa.id == mesa_id).first()
    if db_mesa:
        db.delete(db_mesa)
        db.commit()  # Adicionado commit que estava faltando
    return db_mesa
