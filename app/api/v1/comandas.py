from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from decimal import Decimal

from app.core.session import get_db
from app.models import Cliente, Mesa
from app.schemas.comanda_schemas import ComandaCreate, ComandaUpdate, ComandaInResponse, StatusComanda
from app.schemas.pagamento_schemas import PagamentoCreateSchema
from app.schemas.fiado_schemas import FiadoCreate
from app.services import comanda_service
from app.services.comanda_service import get_all_comandas_detailed

router = APIRouter()


@router.post("/", response_model=ComandaInResponse)
async def criar_comanda(
        data: ComandaCreate,
        db_session: AsyncSession = Depends(get_db)
):
    # Se informou cliente, verifica se existe
    if data.id_cliente_associado is not None:
        cliente = await comanda_service.buscar_cliente(db_session, data.id_cliente_associado)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

    # Verifica se mesa existe sempre
    mesa = await comanda_service.buscar_mesa(db_session, data.id_mesa)
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")

    # Se passou as validações, cria a comanda
    comanda_criada = await comanda_service.create_comanda(db=db_session, comanda_data=data)
    return comanda_criada


@router.get("/{comanda_id}", response_model=ComandaInResponse)
async def obter_comanda_por_id(comanda_id: int, db_session: AsyncSession = Depends(get_db)):
    """
    Retorna os detalhes de uma comanda pelo ID.
    """
    db_comanda = await comanda_service.get_comanda_by_id_detail(db=db_session, comanda_id=comanda_id)
    if not db_comanda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comanda não encontrada")
    return db_comanda


@router.get("/", response_model=List[ComandaInResponse])
async def listar_comandas(
    skip: int = 0,
    limit: int = 100,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Lista todas as comandas com paginação.
    """
    comandas = await get_all_comandas_detailed(db_session, skip=skip, limit=limit)
    return comandas


@router.get("/mesa/{mesa_id}/ativa", response_model=Optional[ComandaInResponse])
async def obter_comanda_ativa_por_mesa(mesa_id: int, db_session: AsyncSession = Depends(get_db)):
    mesa = await comanda_service.buscar_mesa(db_session, mesa_id)
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    comanda_ativa = await comanda_service.get_active_comanda_by_mesa_id(db_session, mesa_id)
    if not comanda_ativa:
        raise HTTPException(status_code=404, detail="Nenhuma comanda ativa encontrada para essa mesa")
    return comanda_ativa

@router.post("/{comanda_id}/registrar-pagamento", response_model=ComandaInResponse)
async def registrar_pagamento(
        comanda_id: int,
        pagamento_data: PagamentoCreateSchema = Body(...),
        db_session: AsyncSession = Depends(get_db)
):
    """
    Registra um pagamento na comanda informada.
    """
    comanda = await comanda_service.get_comanda_by_id(db_session, comanda_id)
    if not comanda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comanda não encontrada")

    if comanda.status_comanda in [StatusComanda.PAGA_TOTALMENTE, StatusComanda.CANCELADA, StatusComanda.FECHADA]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Comanda já está {comanda.status_comanda.value}")

    pagamento_data.id_comanda = comanda_id
    return await comanda_service.registrar_pagamento_na_comanda(db_session, comanda_id, pagamento_data)


@router.post("/{comanda_id}/registrar-fiado", response_model=ComandaInResponse)
async def registrar_fiado(
        comanda_id: int,
        fiado_data: FiadoCreate = Body(...),
        db_session: AsyncSession = Depends(get_db)
):
    """
    Registra o saldo da comanda como fiado para o cliente informado.
    """
    comanda = await comanda_service.get_comanda_by_id(db_session, comanda_id)
    if not comanda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comanda não encontrada")

    if comanda.status_comanda == StatusComanda.PAGA_TOTALMENTE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comanda já foi paga totalmente.")
    if comanda.status_comanda == StatusComanda.EM_FIADO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comanda já está em fiado.")

    valor_a_fiar = comanda.valor_total_calculado - comanda.valor_pago
    if valor_a_fiar <= Decimal(0):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Não há saldo devedor para registrar como fiado.")

    fiado_data.id_comanda = comanda_id
    fiado_data.valor_original = valor_a_fiar
    fiado_data.valor_devido = valor_a_fiar

    return await comanda_service.registrar_saldo_como_fiado(db_session, comanda_id, fiado_data)


@router.post("/{comanda_id}/fechar", response_model=ComandaInResponse)
async def fechar_comanda(comanda_id: int, db_session: AsyncSession = Depends(get_db)):
    """
    Fecha a comanda. Ela deve estar totalmente paga ou com saldo em fiado.
    """
    updated_comanda = await comanda_service.fechar_comanda(db_session, comanda_id)
    if not updated_comanda:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Não foi possível fechar a comanda. Verifique se está totalmente paga ou com saldo em fiado.")
    return updated_comanda


@router.post("/{comanda_id}/qrcode", response_model=ComandaInResponse)
async def gerar_qrcode(comanda_id: int, db_session: AsyncSession = Depends(get_db)):
    """
    Gera ou retorna o QRCode da comanda.
    """
    comanda = await comanda_service.gerar_ou_obter_qrcode_comanda(db_session, comanda_id)
    if not comanda or not comanda.qr_code_comanda_hash:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Não foi possível gerar ou obter o QRCode para a comanda.")
    return comanda
