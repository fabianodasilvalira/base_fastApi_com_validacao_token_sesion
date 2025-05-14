# app/routers/pagamento_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.session import get_db_session
from app.schemas.pagamento_schemas import PagamentoResponseSchema  , PagamentoCreateSchema, PagamentoUpdateSchema
from app.services import pagamento_service

router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])

@router.get("/", response_model=List[PagamentoResponseSchema  ])
def listar(db: Session = Depends(get_db_session())):
    return pagamento_service.listar_pagamentos(db)

@router.get("/{pagamento_id}", response_model=PagamentoResponseSchema  )
def obter(pagamento_id: int, db: Session = Depends(get_db_session)):
    pagamento = pagamento_service.obter_pagamento(db, pagamento_id)
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    return pagamento

@router.post("/", response_model=PagamentoResponseSchema  )
def criar(pagamento: PagamentoCreateSchema, db: Session = Depends(get_db_session)):
    return pagamento_service.criar_pagamento(db, pagamento)

@router.put("/{pagamento_id}", response_model=PagamentoResponseSchema  )
def atualizar(pagamento_id: int, dados: PagamentoUpdateSchema, db: Session = Depends(get_db_session)):
    return pagamento_service.atualizar_pagamento(db, pagamento_id, dados)

@router.delete("/{pagamento_id}", response_model=PagamentoResponseSchema  )
def deletar(pagamento_id: int, db: Session = Depends(get_db_session)):
    return pagamento_service.deletar_pagamento(db, pagamento_id)
