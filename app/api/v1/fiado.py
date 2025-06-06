# app/api/routes/fiado.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.session import get_db
from app.models import User
from app.services import fiado_service
from app.schemas.fiado_schemas import FiadoCreate, FiadoUpdate, FiadoSchema, FiadoPagamentoSchema
from app.api import deps

router = APIRouter()


@router.post("/", response_model=FiadoSchema, status_code=status.HTTP_201_CREATED, summary="Criar novo fiado")
async def criar_fiado(
    fiado_data: FiadoCreate,
    db: AsyncSession = Depends(get_db),
    #usuario_atual: User = Depends(deps.get_current_active_superuser)
):
    """
    Cria um novo registro de fiado.
    """
    try:
        # Se não foi informado, assume o usuário logado como registrador
        if not fiado_data.id_usuario_registrou:
            fiado_data.id_usuario_registrou = usuario_atual.id

        return await fiado_service.create_fiado(db=db, fiado_data=fiado_data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Erro ao criar fiado: {str(e)}")


@router.get("/", response_model=List[FiadoSchema], summary="Obter todos os fiados")
async def obter_fiados(
    db: AsyncSession = Depends(get_db),
    #usuario_atual: User = Depends(deps.get_current_active_superuser)
):
    """
    Retorna todos os fiados cadastrados.
    """
    try:
        return await fiado_service.get_fiado_all(db)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar fiados: {str(e)}"
        )


@router.get("/{fiado_id}", response_model=FiadoSchema, summary="Obter fiado por ID")
async def obter_fiado_por_id(
        fiado_id: int,
        db: AsyncSession = Depends(get_db),
        #usuario_atual: User = Depends(deps.get_current_active_superuser)
):
    """
    Retorna os dados de um fiado pelo ID.

    - **fiado_id**: ID único do fiado a ser consultado
    """
    try:
        return await fiado_service.get_fiado_by_id(db, fiado_id=fiado_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao buscar fiado: {str(e)}")


@router.put("/{fiado_id}", response_model=FiadoSchema, summary="Atualizar fiado")
async def atualizar_fiado(
        fiado_id: int,
        fiado_data: FiadoUpdate,
        db: AsyncSession = Depends(get_db),
        usuario_atual=Depends(deps.get_current_active_user)
):
    """
    Atualiza as informações de um fiado específico.

    - **fiado_id**: ID único do fiado a ser atualizado
    - **fiado_data**: Dados atualizados do fiado
    """
    try:
        return await fiado_service.update_fiado(db, fiado_id=fiado_id, fiado_update_data=fiado_data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Erro ao atualizar fiado: {str(e)}")


@router.get("/cliente/{cliente_id}", response_model=List[FiadoSchema], summary="Listar fiados por cliente")
async def listar_fiados_por_cliente(
        cliente_id: int,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        #usuario_atual=Depends(deps.get_current_active_user)
):
    """
    Lista todos os registros de fiado (pendentes e pagos) de um cliente específico.

    - **cliente_id**: ID único do cliente
    - **skip**: Número de registros para pular (paginação)
    - **limit**: Número máximo de registros a retornar (paginação)
    """
    try:
        fiados = await fiado_service.get_fiados_by_cliente_id(db, cliente_id=cliente_id, skip=skip, limit=limit)
        return fiados or []
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Erro ao listar fiados: {str(e)}")


@router.post("/{fiado_id}/pagamento", response_model=FiadoSchema, summary="Registrar pagamento em fiado")
async def registrar_pagamento_fiado(
        fiado_id: int,
        pagamento_data: FiadoPagamentoSchema,
        db: AsyncSession = Depends(get_db),
        usuario_atual=Depends(deps.get_current_active_user)
):
    """
    Registra um pagamento (parcial ou total) em um débito de fiado existente.

    - **fiado_id**: ID único do fiado
    - **valor_pago**: Valor do pagamento realizado
    - **observacoes**: Observações sobre o pagamento (opcional)
    """
    try:
        # Registra automaticamente o usuário atual como quem registrou o pagamento
        if not pagamento_data.id_usuario_registrou:
            pagamento_data.id_usuario_registrou = usuario_atual.id

        updated_fiado = await fiado_service.registrar_pagamento_em_fiado(
            db,
            fiado_id=fiado_id,
            valor_pago=pagamento_data.valor_pago,
            id_usuario_registrou=pagamento_data.id_usuario_registrou,
            observacoes=pagamento_data.observacoes
        )
        return updated_fiado
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Erro ao registrar pagamento: {str(e)}")
