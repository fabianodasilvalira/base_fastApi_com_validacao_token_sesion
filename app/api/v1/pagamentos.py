from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.session import get_db
from app.schemas.pagamento_schemas import (
    PagamentoResponseSchema,
    PagamentoCreateSchema,
    PagamentoUpdateSchema, MessageSchema
)
from app.services.pagamento_service import (
    listar_pagamentos,
    obter_pagamento,
    criar_pagamento,
    atualizar_pagamento,
    deletar_pagamento
)

# Removendo o prefixo "/pagamentos" do router para evitar duplicação
router = APIRouter()

@router.get("/", response_model=List[PagamentoResponseSchema])
async def read_multiple(skip: int = 0, limit: int = 100, db_session: AsyncSession = Depends(get_db)):
    """
    Retorna a lista de todos os pagamentos cadastrados.

    - **skip**: Número de registros a pular (paginação).
    - **limit**: Número máximo de registros a retornar.
    - **Retorno**: Lista de pagamentos
    """
    return await listar_pagamentos(db_session, skip, limit)

@router.get("/{pagamento_id}", response_model=PagamentoResponseSchema)
async def read(pagamento_id: int, db_session: AsyncSession = Depends(get_db)):
    """
    Retorna os dados de um pagamento específico.

    - **pagamento_id**: ID do pagamento a ser consultado
    - **Retorno**: Dados do pagamento
    - **Erro**: 404 se o pagamento não for encontrado
    """
    pagamento = await obter_pagamento(db_session, pagamento_id)
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    return pagamento

@router.post("/", response_model=PagamentoResponseSchema)
async def create(pagamento: PagamentoCreateSchema, db_session: AsyncSession = Depends(get_db)):
    """
    Cria um novo pagamento no sistema.

    - **pagamento**: Dados do novo pagamento
    - **Retorno**: Pagamento criado
    """
    return await criar_pagamento(db_session, pagamento)

# @router.put("/{pagamento_id}", response_model=PagamentoResponseSchema)
# async def update(pagamento_id: int, dados: PagamentoUpdateSchema, db_session: AsyncSession = Depends(get_db)):
#     """
#     Atualiza os dados de um pagamento existente.
#
#     - **pagamento_id**: ID do pagamento a ser atualizado
#     - **dados**: Dados atualizados
#     - **Retorno**: Pagamento atualizado
#     - **Erro**: 404 se o pagamento não for encontrado
#     """
#     pagamento = await atualizar_pagamento(db_session, pagamento_id, dados)
#     if not pagamento:
#         raise HTTPException(status_code=404, detail="Pagamento não encontrado")
#     return pagamento

@router.delete("/{pagamento_id}", response_model=MessageSchema)
async def delete(pagamento_id: int, db_session: AsyncSession = Depends(get_db)):
    """
    Remove um pagamento do sistema.

    - **pagamento_id**: ID do pagamento a ser excluído
    - **Retorno**: Pagamento excluído
    - **Erro**: 404 se o pagamento não for encontrado
    """
    pagamento = await deletar_pagamento(db_session, pagamento_id)
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    return {"message": f"Pagamento ID {pagamento_id} deletado com sucesso e valores da comanda atualizados."}