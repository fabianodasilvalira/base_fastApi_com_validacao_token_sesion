from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.session import get_db_session
from app.schemas.pagamento_schemas import (
    PagamentoResponseSchema,
    PagamentoCreateSchema,
    PagamentoUpdateSchema
)
from app.services import pagamento_service

router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])

@router.get("/", response_model=List[PagamentoResponseSchema])
def listar_pagamentos(db: Session = Depends(get_db_session)):
    """
    Retorna a lista de todos os pagamentos cadastrados.

    - **Retorno**: Lista de pagamentos
    """
    return pagamento_service.listar_pagamentos(db)

@router.get("/{pagamento_id}", response_model=PagamentoResponseSchema)
def obter_pagamento(pagamento_id: int, db: Session = Depends(get_db_session)):
    """
    Retorna os dados de um pagamento específico.

    - **parâmetro**: `pagamento_id` - ID do pagamento a ser consultado
    - **Retorno**: Dados do pagamento
    - **Erro**: 404 se o pagamento não for encontrado
    """
    pagamento = pagamento_service.obter_pagamento(db, pagamento_id)
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    return pagamento

@router.post("/", response_model=PagamentoResponseSchema)
def criar_pagamento(pagamento: PagamentoCreateSchema, db: Session = Depends(get_db_session)):
    """
    Cria um novo pagamento no sistema.

    - **Corpo da requisição**: Dados do novo pagamento
    - **Retorno**: Pagamento criado
    """
    return pagamento_service.criar_pagamento(db, pagamento)

@router.put("/{pagamento_id}", response_model=PagamentoResponseSchema)
def atualizar_pagamento(pagamento_id: int, dados: PagamentoUpdateSchema, db: Session = Depends(get_db_session)):
    """
    Atualiza os dados de um pagamento existente.

    - **parâmetro**: `pagamento_id` - ID do pagamento a ser atualizado
    - **Corpo da requisição**: Dados atualizados
    - **Retorno**: Pagamento atualizado
    """
    return pagamento_service.atualizar_pagamento(db, pagamento_id, dados)

@router.delete("/{pagamento_id}", response_model=PagamentoResponseSchema)
def deletar_pagamento(pagamento_id: int, db: Session = Depends(get_db_session)):
    """
    Remove um pagamento do sistema.

    - **parâmetro**: `pagamento_id` - ID do pagamento a ser excluído
    - **Retorno**: Pagamento excluído
    - **Erro**: 404 se o pagamento não for encontrado
    """
    return pagamento_service.deletar_pagamento(db, pagamento_id)
