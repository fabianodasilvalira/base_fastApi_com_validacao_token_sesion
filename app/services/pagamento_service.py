# app/services/pagamento_service.py
from sqlalchemy.orm import Session
from app.db.models.pagamento import Pagamento
from app.schemas.pagamento import PagamentoCreate, PagamentoUpdate

def listar_pagamentos(db: Session):
    return db.query(Pagamento).all()

def obter_pagamento(db: Session, pagamento_id: int):
    return db.query(Pagamento).filter(Pagamento.id == pagamento_id).first()

def criar_pagamento(db: Session, pagamento: PagamentoCreate):
    novo_pagamento = Pagamento(**pagamento.dict())
    db.add(novo_pagamento)
    db.commit()
    db.refresh(novo_pagamento)
    return novo_pagamento

def atualizar_pagamento(db: Session, pagamento_id: int, dados: PagamentoUpdate):
    pagamento_db = obter_pagamento(db, pagamento_id)
    if pagamento_db:
        for key, value in dados.dict().items():
            setattr(pagamento_db, key, value)
        db.commit()
        db.refresh(pagamento_db)
    return pagamento_db

def deletar_pagamento(db: Session, pagamento_id: int):
    pagamento_db = obter_pagamento(db, pagamento_id)
    if pagamento_db:
        db.delete(pagamento_db)
        db.commit()
    return pagamento_db
