# app/api/v1/comandas.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession # Alterado para AsyncSession
from typing import List, Optional
from decimal import Decimal

from app.core.session import get_db_session
from app.schemas.comanda_schemas import ComandaCreate, ComandaUpdate, ComandaInResponse, StatusComanda
from app.schemas.pagamento_schemas import PagamentoCreateSchema, MetodoPagamento # Adicionado MetodoPagamento
from app.schemas.fiado_schemas import FiadoCreate # Adicionado FiadoCreate
from app.services import comanda_service, pagamento_service, fiado_service # Adicionado fiado_service
from app.models.comanda import Comanda as ComandaModel # Para checagem de status

router = APIRouter(
    prefix="/comandas",
    tags=["Comandas"],
)

@router.post("/", response_model=ComandaInResponse)
async def create_new_comanda(comanda: ComandaCreate, db: AsyncSession = Depends(get_db_session)):
    db_comanda = await comanda_service.create_comanda(db=db, comanda_data=comanda) # Ajustado para async e nome do service
    return db_comanda

@router.put("/{comanda_id}", response_model=ComandaInResponse)
async def update_existing_comanda(comanda_id: int, comanda_update_data: ComandaUpdate, db: AsyncSession = Depends(get_db_session)):
    db_comanda = await comanda_service.update_comanda(db=db, comanda_id=comanda_id, comanda_update_data=comanda_update_data)
    if not db_comanda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comanda não encontrada")
    return db_comanda

@router.get("/{comanda_id}", response_model=ComandaInResponse)
async def get_comanda(comanda_id: int, db: AsyncSession = Depends(get_db_session)):
    db_comanda = await comanda_service.get_comanda_by_id_detail(db=db, comanda_id=comanda_id) # Supõe um método que traga detalhes
    if not db_comanda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comanda não encontrada")
    return db_comanda

@router.get("/", response_model=List[ComandaInResponse])
async def get_comandas(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db_session)):
    db_comandas = await comanda_service.get_all_comandas_detailed(db=db, skip=skip, limit=limit)
    return db_comandas

@router.get("/mesa/{mesa_id}/ativa", response_model=Optional[ComandaInResponse])
async def get_active_comanda_for_mesa(mesa_id: str, db: AsyncSession = Depends(get_db_session)):
    comanda = await comanda_service.get_active_comanda_by_mesa_id(db, mesa_id)
    if not comanda:
        # Retorna 204 ou 404 dependendo da preferência. 404 se nenhuma ativa é um "não encontrado".
        # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma comanda ativa encontrada para esta mesa.")
        return None # FastAPI retornará 200 com corpo nulo, ou pode-se usar Response(status_code=204)
    return comanda

@router.post("/{comanda_id}/registrar-pagamento", response_model=ComandaInResponse)
async def registrar_pagamento_comanda(
    comanda_id: int,
    valor_pago: Decimal,
    metodo_pagamento: MetodoPagamento,
    id_cliente: Optional[int] = None, # Necessário se o pagamento for associado a um cliente específico
    id_usuario_registrou: Optional[int] = None, # ID do usuário (caixa) que registrou
    observacoes: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    comanda = await comanda_service.get_comanda_by_id(db, comanda_id)
    if not comanda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comanda não encontrada")

    if comanda.status_comanda in [StatusComanda.PAGA_TOTALMENTE, StatusComanda.CANCELADA, StatusComanda.FECHADA]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Comanda já está {comanda.status_comanda.value}")

    pagamento_data = PagamentoCreateSchema(
        id_comanda=comanda_id,
        id_cliente=id_cliente,
        id_usuario_registrou=id_usuario_registrou,
        valor_pago=valor_pago,
        metodo_pagamento=metodo_pagamento,
        observacoes=observacoes
    )
    
    updated_comanda = await comanda_service.registrar_pagamento_na_comanda(db, comanda_id, pagamento_data)
    return updated_comanda

@router.post("/{comanda_id}/registrar-fiado", response_model=ComandaInResponse)
async def registrar_fiado_comanda(
    comanda_id: int,
    id_cliente: int, # Fiado sempre precisa de um cliente
    id_usuario_registrou: Optional[int] = None,
    observacoes_fiado: Optional[str] = None,
    data_vencimento: Optional[str] = None, # Formato YYYY-MM-DD
    db: AsyncSession = Depends(get_db_session)
):
    comanda = await comanda_service.get_comanda_by_id(db, comanda_id)
    if not comanda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comanda não encontrada")

    if comanda.status_comanda == StatusComanda.PAGA_TOTALMENTE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comanda já foi paga totalmente.")
    if comanda.status_comanda == StatusComanda.EM_FIADO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comanda já está em fiado.")

    valor_a_fiar = comanda.valor_total_calculado - comanda.valor_pago
    if valor_a_fiar <= Decimal(0):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Não há saldo devedor para registrar como fiado. Considere quitar a comanda.")

    fiado_data = FiadoCreate(
        id_comanda=comanda_id,
        id_cliente=id_cliente,
        id_usuario_registrou=id_usuario_registrou,
        valor_original=valor_a_fiar,
        valor_devido=valor_a_fiar, # Inicialmente o valor devido é o total a fiar
        observacoes=observacoes_fiado,
        data_vencimento=data_vencimento
    )

    updated_comanda = await comanda_service.registrar_saldo_como_fiado(db, comanda_id, fiado_data)
    return updated_comanda

@router.post("/{comanda_id}/fechar", response_model=ComandaInResponse)
async def fechar_comanda_endpoint(
    comanda_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Fecha uma comanda. A comanda deve estar PAGA_TOTALMENTE ou EM_FIADO (se o saldo foi para fiado).
    Pode envolver lógicas como desassociar cliente da mesa, atualizar status da mesa.
    """
    updated_comanda = await comanda_service.fechar_comanda(db, comanda_id)
    if not updated_comanda:
         # O service.fechar_comanda deve levantar HTTPException se não puder fechar
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Não foi possível fechar a comanda. Verifique o status e os pagamentos.")
    return updated_comanda

# Adicionar rota para gerar QRCode para a comanda (se o QR for específico da comanda)
@router.post("/{comanda_id}/qrcode", response_model=ComandaInResponse) # Ou um schema específico para QR
async def gerar_qrcode_comanda(
    comanda_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    comanda = await comanda_service.gerar_ou_obter_qrcode_comanda(db, comanda_id)
    if not comanda or not comanda.qr_code_comanda_hash:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Não foi possível gerar ou obter o QRCode para a comanda.")
    return comanda

