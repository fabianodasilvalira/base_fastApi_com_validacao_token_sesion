from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.session import get_db_session
from app.services import fiado_service
from app.schemas.fiado_schemas import FiadoCreate, FiadoUpdate, Fiado as FiadoSchema, FiadoPagamentoSchema

router = APIRouter()

@router.post("/", response_model=FiadoSchema)
async def criar_fiado(fiado_data: FiadoCreate, db: AsyncSession = Depends(get_db_session)):
    """
    Cria um novo registro de fiado manualmente.
    """
    try:
        return await fiado_service.create_fiado(db=db, fiado_data=fiado_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{fiado_id}", response_model=FiadoSchema)
async def obter_fiado_por_id(fiado_id: int, db: AsyncSession = Depends(get_db_session)):
    """
    Retorna os dados de um fiado pelo ID.
    """
    db_fiado = await fiado_service.get_fiado_by_id(db, fiado_id=fiado_id)
    if db_fiado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de fiado não encontrado")
    return db_fiado

@router.put("/{fiado_id}", response_model=FiadoSchema)
async def atualizar_fiado(fiado_id: int, fiado_data: FiadoUpdate, db: AsyncSession = Depends(get_db_session)):
    """
    Atualiza as informações de um fiado específico.
    """
    db_fiado = await fiado_service.update_fiado(db, fiado_id=fiado_id, fiado_update_data=fiado_data)
    if db_fiado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de fiado não encontrado para atualização")
    return db_fiado

@router.get("/cliente/{cliente_id}", response_model=List[FiadoSchema])
async def listar_fiados_por_cliente(cliente_id: int, db: AsyncSession = Depends(get_db_session)):
    """
    Lista todos os registros de fiado (pendentes e pagos) de um cliente específico.
    """
    fiados = await fiado_service.get_fiados_by_cliente_id(db, cliente_id=cliente_id)
    if not fiados:
        return []
    return fiados

@router.post("/{fiado_id}/registrar-pagamento", response_model=FiadoSchema)
async def registrar_pagamento_fiado(
    fiado_id: int,
    pagamento_data: FiadoPagamentoSchema,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Registra um pagamento (parcial ou total) em um débito de fiado existente.
    """
    updated_fiado = await fiado_service.registrar_pagamento_em_fiado(
        db,
        fiado_id=fiado_id,
        valor_pago=pagamento_data.valor_pago,
        id_usuario_registrou=pagamento_data.id_usuario_registrou,
        observacoes=pagamento_data.observacoes
    )
    if not updated_fiado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Não foi possível registrar o pagamento no fiado.")
    return updated_fiado
