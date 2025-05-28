import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.session import get_db
from app.schemas.comanda_schemas import ComandaCreate, ComandaUpdate, ComandaInResponse, QRCodeHashResponse
from app.schemas.pagamento_schemas import PagamentoCreateSchema
from app.schemas.fiado_schemas import FiadoCreate
from app.services.comanda_service import ComandaService, ComandaValidationError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=ComandaInResponse, status_code=status.HTTP_201_CREATED)
async def criar_comanda(
        data: ComandaCreate,
        db_session: AsyncSession = Depends(get_db)
):
    """
    Cria uma nova comanda.

    Validações aplicadas:
    - Mesa deve existir e não estar ocupada
    - Cliente (se informado) deve existir e não ter comanda ativa
    """
    try:
        comanda_criada = await ComandaService.criar_comanda(db_session, data)

        # Serialização segura
        comanda_dict = {
            "id": comanda_criada.id,
            "id_mesa": comanda_criada.id_mesa,
            "id_cliente_associado": comanda_criada.id_cliente_associado,
            "status_comanda": comanda_criada.status_comanda,
            "valor_total_calculado": comanda_criada.valor_total_calculado,
            "percentual_taxa_servico": comanda_criada.percentual_taxa_servico,
            "valor_taxa_servico": comanda_criada.valor_taxa_servico,
            "valor_desconto": comanda_criada.valor_desconto,
            "valor_final_comanda": comanda_criada.valor_final_comanda,
            "valor_pago": comanda_criada.valor_pago,
            "valor_fiado": comanda_criada.valor_fiado,
            "valor_credito_usado": comanda_criada.valor_credito_usado,
            "observacoes": comanda_criada.observacoes,
            "qr_code_comanda_hash": comanda_criada.qr_code_comanda_hash,
            "created_at": comanda_criada.created_at,
            "updated_at": comanda_criada.updated_at,
        }

        return ComandaInResponse(**comanda_dict)

    except ComandaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erro inesperado ao criar comanda: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")


@router.get("/{comanda_id}", response_model=ComandaInResponse)
async def obter_comanda_por_id(
        comanda_id: int,
        db_session: AsyncSession = Depends(get_db)
):
    """Obtém uma comanda específica por ID"""
    try:
        comanda = await ComandaService.buscar_comanda_completa(db_session, comanda_id)
        if not comanda:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comanda não encontrada")

        # Serialização mais segura - converte para dict primeiro
        comanda_dict = {
            "id": comanda.id,
            "id_mesa": comanda.id_mesa,
            "id_cliente_associado": comanda.id_cliente_associado,
            "status_comanda": comanda.status_comanda,
            "valor_total_calculado": comanda.valor_total_calculado,
            "percentual_taxa_servico": comanda.percentual_taxa_servico,
            "valor_taxa_servico": comanda.valor_taxa_servico,
            "valor_desconto": comanda.valor_desconto,
            "valor_final_comanda": comanda.valor_final_comanda,
            "valor_pago": comanda.valor_pago,
            "valor_fiado": comanda.valor_fiado,
            "valor_credito_usado": comanda.valor_credito_usado,
            "observacoes": comanda.observacoes,
            "qr_code_comanda_hash": comanda.qr_code_comanda_hash,
            "created_at": comanda.created_at,
            "updated_at": comanda.updated_at,
        }

        # Adicionar relacionamentos se existirem
        if hasattr(comanda, 'mesa') and comanda.mesa:
            comanda_dict["mesa"] = {
                "id": comanda.mesa.id,
                "numero": getattr(comanda.mesa, 'numero', None),
                "capacidade": getattr(comanda.mesa, 'capacidade', None),
                "descricao": getattr(comanda.mesa, 'descricao', None),
                "status": getattr(comanda.mesa, 'status', None),
            }

        if hasattr(comanda, 'cliente') and comanda.cliente:
            comanda_dict["cliente"] = {
                "id": comanda.cliente.id,
                "nome": getattr(comanda.cliente, 'nome', None),
                "telefone": getattr(comanda.cliente, 'telefone', None),
                "email": getattr(comanda.cliente, 'email', None),
                "cpf": getattr(comanda.cliente, 'cpf', None),
            }

        return ComandaInResponse(**comanda_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar comanda {comanda_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")


@router.get("/", response_model=List[ComandaInResponse])
async def listar_comandas(
        skip: int = 0,
        limit: int = 100,
        db_session: AsyncSession = Depends(get_db)
):
    """Lista todas as comandas com paginação"""
    try:
        comandas = await ComandaService.listar_comandas(db_session, skip=skip, limit=limit)
        return comandas
    except Exception as e:
        logger.error(f"❌ Erro ao listar comandas: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")


@router.get("/mesa/{mesa_id}/ativa", response_model=Optional[ComandaInResponse])
async def obter_comanda_ativa_por_mesa(
        mesa_id: int,
        db_session: AsyncSession = Depends(get_db)
):
    """Obtém a comanda ativa de uma mesa específica"""
    try:
        comanda_ativa = await ComandaService.buscar_comanda_ativa_por_mesa(db_session, mesa_id)
        if not comanda_ativa:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Nenhuma comanda ativa encontrada para essa mesa")

        return comanda_ativa
    except ComandaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar comanda ativa da mesa {mesa_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")


@router.post("/{comanda_id}/registrar-pagamento", response_model=ComandaInResponse)
async def registrar_pagamento(
        comanda_id: int,
        pagamento_data: PagamentoCreateSchema = Body(...),
        db_session: AsyncSession = Depends(get_db)
):
    """Registra um pagamento na comanda"""
    try:
        comanda_atualizada = await ComandaService.registrar_pagamento(db_session, comanda_id, pagamento_data)
        return comanda_atualizada
    except ComandaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erro ao registrar pagamento na comanda {comanda_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")


@router.post("/{comanda_id}/registrar-fiado", response_model=ComandaInResponse)
async def registrar_fiado(
        comanda_id: int,
        fiado_data: FiadoCreate = Body(...),
        db_session: AsyncSession = Depends(get_db)
):
    """Registra o saldo da comanda como fiado para o cliente"""
    try:
        comanda_atualizada = await ComandaService.registrar_fiado(db_session, comanda_id, fiado_data)
        return comanda_atualizada
    except ComandaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erro ao registrar fiado na comanda {comanda_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")


@router.post("/{comanda_id}/fechar", response_model=ComandaInResponse)
async def fechar_comanda(
        comanda_id: int,
        db_session: AsyncSession = Depends(get_db)
):
    """Fecha a comanda (deve estar totalmente paga ou com saldo em fiado)"""
    try:
        comanda_fechada = await ComandaService.fechar_comanda(db_session, comanda_id)
        return comanda_fechada
    except ComandaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erro ao fechar comanda {comanda_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")


@router.post("/{comanda_id}/qrcode", response_model=QRCodeHashResponse)
async def gerar_qrcode(
        comanda_id: int,
        db_session: AsyncSession = Depends(get_db)
):
    """Gera ou retorna o QR Code da comanda"""
    try:
        comanda = await ComandaService.gerar_qrcode(db_session, comanda_id)
        return {"qr_code_comanda_hash": comanda.qr_code_comanda_hash}
    except ComandaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erro ao gerar QR Code para comanda {comanda_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")


@router.post("/{comanda_id}/recalcular", response_model=ComandaInResponse)
async def recalcular_totais(
        comanda_id: int,
        db_session: AsyncSession = Depends(get_db)
):
    """Endpoint para forçar recálculo dos totais da comanda"""
    try:
        comanda_atualizada = await ComandaService.recalcular_totais_comanda(db_session, comanda_id, fazer_commit=True)
        if not comanda_atualizada:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comanda não encontrada")

        return comanda_atualizada
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao recalcular totais da comanda {comanda_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")
