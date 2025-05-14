from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from decimal import Decimal

from app.core.session import get_db_session
from app.schemas.comanda_schemas import ComandaCreate, ComandaUpdate, ComandaInResponse, StatusComanda
from app.schemas.pagamento_schemas import PagamentoCreateSchema, MetodoPagamento
from app.schemas.fiado_schemas import FiadoCreate
from app.services import comanda_service, pagamento_service, fiado_service
from app.models.comanda import Comanda as ComandaModel

router = APIRouter(
    prefix="/comandas",
    tags=["Comandas"],
)


@router.post("/", response_model=ComandaInResponse)
async def criar_comanda(comanda: ComandaCreate, db: AsyncSession = Depends(get_db_session)):
    """
    Cria uma nova comanda.
    """
    return await comanda_service.create_comanda(db=db, comanda_data=comanda)


@router.put("/{comanda_id}", response_model=ComandaInResponse)
async def atualizar_comanda(comanda_id: int, comanda_update_data: ComandaUpdate,
                            db: AsyncSession = Depends(get_db_session)):
    """
    Atualiza os dados de uma comanda existente.
    """
    db_comanda = await comanda_service.update_comanda(db=db, comanda_id=comanda_id,
                                                      comanda_update_data=comanda_update_data)
    if not db_comanda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comanda não encontrada")
    return db_comanda


@router.get("/{comanda_id}", response_model=ComandaInResponse)
async def obter_comanda_por_id(comanda_id: int, db: AsyncSession = Depends(get_db_session)):
    """
    Retorna os detalhes de uma comanda pelo ID.
    """
    db_comanda = await comanda_service.get_comanda_by_id_detail(db=db, comanda_id=comanda_id)
    if not db_comanda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comanda não encontrada")
    return db_comanda


@router.get("/", response_model=List[ComandaInResponse])
async def listar_comandas(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db_session)):
    """
    Lista todas as comandas com paginação.
    """
    return await comanda_service.get_all_comandas_detailed(db=db, skip=skip, limit=limit)


@router.get("/mesa/{mesa_id}/ativa", response_model=Optional[ComandaInResponse])
async def obter_comanda_ativa_por_mesa(mesa_id: str, db: AsyncSession = Depends(get_db_session)):
    """
    Retorna a comanda ativa de uma mesa específica.
    """
    return await comanda_service.get_active_comanda_by_mesa_id(db, mesa_id)


@router.post("/{comanda_id}/registrar-pagamento", response_model=ComandaInResponse)
async def registrar_pagamento(
        comanda_id: int,
        valor_pago: Decimal,
        metodo_pagamento: MetodoPagamento,
        id_cliente: Optional[int] = None,
        id_usuario_registrou: Optional[int] = None,
        observacoes: Optional[str] = None,
        db: AsyncSession = Depends(get_db_session)
):
    """
    Registra um pagamento na comanda informada.
    """
    comanda = await comanda_service.get_comanda_by_id(db, comanda_id)
    if not comanda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comanda não encontrada")

    if comanda.status_comanda in [StatusComanda.PAGA_TOTALMENTE, StatusComanda.CANCELADA, StatusComanda.FECHADA]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Comanda já está {comanda.status_comanda.value}")

    pagamento_data = PagamentoCreateSchema(
        id_comanda=comanda_id,
        id_cliente=id_cliente,
        id_usuario_registrou=id_usuario_registrou,
        valor_pago=valor_pago,
        metodo_pagamento=metodo_pagamento,
        observacoes=observacoes
    )

    return await comanda_service.registrar_pagamento_na_comanda(db, comanda_id, pagamento_data)


@router.post("/{comanda_id}/registrar-fiado", response_model=ComandaInResponse)
async def registrar_fiado(
        comanda_id: int,
        id_cliente: int,
        id_usuario_registrou: Optional[int] = None,
        observacoes_fiado: Optional[str] = None,
        data_vencimento: Optional[str] = None,
        db: AsyncSession = Depends(get_db_session)
):
    """
    Registra o saldo da comanda como fiado para o cliente informado.
    """
    comanda = await comanda_service.get_comanda_by_id(db, comanda_id)
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

    fiado_data = FiadoCreate(
        id_comanda=comanda_id,
        id_cliente=id_cliente,
        id_usuario_registrou=id_usuario_registrou,
        valor_original=valor_a_fiar,
        valor_devido=valor_a_fiar,
        observacoes=observacoes_fiado,
        data_vencimento=data_vencimento
    )

    return await comanda_service.registrar_saldo_como_fiado(db, comanda_id, fiado_data)


@router.post("/{comanda_id}/fechar", response_model=ComandaInResponse)
async def fechar_comanda(comanda_id: int, db: AsyncSession = Depends(get_db_session)):
    """
    Fecha a comanda. Ela deve estar totalmente paga ou com saldo em fiado.
    """
    updated_comanda = await comanda_service.fechar_comanda(db, comanda_id)
    if not updated_comanda:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Não foi possível fechar a comanda.")
    return updated_comanda


@router.post("/{comanda_id}/qrcode", response_model=ComandaInResponse)
async def gerar_qrcode(comanda_id: int, db: AsyncSession = Depends(get_db_session)):
    """
    Gera ou retorna o QRCode da comanda.
    """
    comanda = await comanda_service.gerar_ou_obter_qrcode_comanda(db, comanda_id)
    if not comanda or not comanda.qr_code_comanda_hash:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Não foi possível gerar ou obter o QRCode para a comanda.")
    return comanda
