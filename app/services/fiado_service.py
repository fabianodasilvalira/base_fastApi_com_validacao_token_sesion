# app/services/fiado.py
from sqlalchemy.orm import Session
from app.models.fiado import Fiado
from app.schemas.fiado_schemas import FiadoCreate, FiadoUpdate

def get_fiado(db: Session, fiado_id: int):
    return db.query(Fiado).filter(Fiado.id == fiado_id).first()

def create_fiado(db: Session, fiado: FiadoCreate):
    db_fiado = Fiado(
        id_comanda=fiado.id_comanda,
        id_cliente=fiado.id_cliente,
        id_usuario_registrou=fiado.id_usuario_registrou,
        valor_original=fiado.valor_original,
        valor_devido=fiado.valor_devido,
        status_fiado=fiado.status_fiado,
        data_vencimento=fiado.data_vencimento,
        observacoes=fiado.observacoes,
    )
    db.add(db_fiado)
    db.commit()
    db.refresh(db_fiado)
    return db_fiado

def update_fiado(db: Session, fiado_id: int, fiado: FiadoUpdate):
    db_fiado = db.query(Fiado).filter(Fiado.id == fiado_id).first()
    if db_fiado:
        db_fiado.valor_original = fiado.valor_original
        db_fiado.valor_devido = fiado.valor_devido
        db_fiado.status_fiado = fiado.status_fiado
        db_fiado.data_vencimento = fiado.data_vencimento
        db_fiado.observacoes = fiado.observacoes
        db.commit()
        db.refresh(db_fiado)
    return db_fiado
