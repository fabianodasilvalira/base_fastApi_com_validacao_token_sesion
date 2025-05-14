# app/services/comanda_service.py
from sqlalchemy.orm import Session
from app.models.comanda import Comanda, StatusComanda
from app.schemas.comanda_schemas import ComandaCreate, ComandaUpdate
from uuid import uuid4


def create_comanda(db: Session, comanda: ComandaCreate) -> Comanda:
    db_comanda = Comanda(
        id=str(uuid4()),  # Gerando um ID único
        id_mesa=comanda.id_mesa,
        id_cliente_associado=comanda.id_cliente_associado,
        status_comanda=comanda.status_comanda,
        valor_total_calculado=comanda.valor_total_calculado,
        valor_pago=comanda.valor_pago,
        valor_fiado=comanda.valor_fiado,
        observacoes=comanda.observacoes
    )
    db.add(db_comanda)
    db.commit()
    db.refresh(db_comanda)
    return db_comanda


def update_comanda(db: Session, comanda_id: str, comanda: ComandaUpdate) -> Comanda:
    db_comanda = db.query(Comanda).filter(Comanda.id == comanda_id).first()
    if db_comanda:
        if comanda.id_mesa:
            db_comanda.id_mesa = comanda.id_mesa
        if comanda.id_cliente_associado:
            db_comanda.id_cliente_associado = comanda.id_cliente_associado
        if comanda.status_comanda:
            db_comanda.status_comanda = comanda.status_comanda
        if comanda.valor_total_calculado is not None:
            db_comanda.valor_total_calculado = comanda.valor_total_calculado
        if comanda.valor_pago is not None:
            db_comanda.valor_pago = comanda.valor_pago
        if comanda.valor_fiado is not None:
            db_comanda.valor_fiado = comanda.valor_fiado
        if comanda.observacoes:
            db_comanda.observacoes = comanda.observacoes

        db.commit()
        db.refresh(db_comanda)
        return db_comanda
    return None


def get_comanda_by_id(db: Session, comanda_id: str) -> Comanda:
    return db.query(Comanda).filter(Comanda.id == comanda_id).first()


def get_all_comandas(db: Session, skip: int = 0, limit: int = 100) -> list:
    return db.query(Comanda).offset(skip).limit(limit).all()
