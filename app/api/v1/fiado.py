# app/api/v1/fiado.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession # Alterado para AsyncSession
from typing import List, Optional
from decimal import Decimal

from app.core.session import get_db_session
from app.services import fiado_service
from app.schemas.fiado_schemas import FiadoCreate, FiadoUpdate, Fiado as FiadoSchema, FiadoPagamentoSchema

router = APIRouter(prefix="/fiados", tags=["Fiados"])

@router.post("/", response_model=FiadoSchema)
async def create_fiado_endpoint(fiado_data: FiadoCreate, db: AsyncSession = Depends(get_db_session)):
    # Esta rota é mais para criação manual de um fiado, o fluxo principal vem da comanda.
    # Mas pode ser útil para registrar dívidas antigas, por exemplo.
    try:
        return await fiado_service.create_fiado(db=db, fiado_data=fiado_data)
    except Exception as e:
        # Idealmente, o service trataria exceções específicas e levantaria HTTPExceptions
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{fiado_id}", response_model=FiadoSchema)
async def read_fiado_endpoint(fiado_id: int, db: AsyncSession = Depends(get_db_session)):
    db_fiado = await fiado_service.get_fiado_by_id(db, fiado_id=fiado_id)
    if db_fiado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de fiado não encontrado")
    return db_fiado

@router.put("/{fiado_id}", response_model=FiadoSchema)
async def update_fiado_endpoint(fiado_id: int, fiado_data: FiadoUpdate, db: AsyncSession = Depends(get_db_session)):
    db_fiado = await fiado_service.update_fiado(db, fiado_id=fiado_id, fiado_update_data=fiado_data)
    if db_fiado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de fiado não encontrado para atualização")
    return db_fiado

@router.get("/cliente/{cliente_id}", response_model=List[FiadoSchema])
async def list_fiados_by_cliente_endpoint(cliente_id: int, db: AsyncSession = Depends(get_db_session)):
    """
    Lista todos os registros de fiado (pendentes e pagos) de um cliente específico.
    """
    fiados = await fiado_service.get_fiados_by_cliente_id(db, cliente_id=cliente_id)
    if not fiados:
        # Pode retornar uma lista vazia ou 404 se o cliente não tiver fiados.
        # Lista vazia é mais comum para "get all by X".
        return []
    return fiados

@router.post("/{fiado_id}/registrar-pagamento", response_model=FiadoSchema)
async def registrar_pagamento_fiado_endpoint(
    fiado_id: int, 
    pagamento_data: FiadoPagamentoSchema, # Schema para receber valor_pago e observacoes
    db: AsyncSession = Depends(get_db_session)
):
    """
    Registra um pagamento (parcial ou total) em um débito de fiado existente.
    Atualiza Fiado.valor_devido e Fiado.status_fiado.
    """
    updated_fiado = await fiado_service.registrar_pagamento_em_fiado(
        db,
        fiado_id=fiado_id,
        valor_pago=pagamento_data.valor_pago,
        id_usuario_registrou=pagamento_data.id_usuario_registrou, # Adicionar ao schema se necessário
        observacoes=pagamento_data.observacoes
    )
    if not updated_fiado:
        # O service deve levantar HTTPException se o fiado não for encontrado ou se houver erro no pagamento
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Não foi possível registrar o pagamento no fiado.")
    return updated_fiado

