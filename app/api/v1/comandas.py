import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from app.core.session import get_db
from app.schemas.comanda_schemas import ComandaCreate, ComandaUpdate, ComandaInResponse, ComandaCreateResponse, \
    QRCodeHashResponse
from app.schemas.pagamento_schemas import PagamentoCreateSchema
from app.schemas.fiado_schemas import FiadoCreate
from app.services.comanda_service import ComandaService, ComandaValidationError

logger = logging.getLogger(__name__)

router = APIRouter()


def _serializar_comanda_segura(comanda) -> dict:
    """✅ CORRIGIDO: Função para serialização segura da comanda"""
    if not comanda:
        return None

    # Garantir que todos os valores monetários sejam Decimal válidos
    def safe_decimal(value, default="0.00"):
        if value is None:
            return Decimal(default)
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return Decimal(default)

    comanda_dict = {
        "id": comanda.id,
        "id_mesa": comanda.id_mesa,
        "id_cliente_associado": comanda.id_cliente_associado,
        "status_comanda": comanda.status_comanda,
        "valor_total_calculado": safe_decimal(comanda.valor_total_calculado),
        "percentual_taxa_servico": safe_decimal(comanda.percentual_taxa_servico, "10.00"),
        "valor_taxa_servico": safe_decimal(comanda.valor_taxa_servico),
        "valor_desconto": safe_decimal(comanda.valor_desconto),
        "valor_final_comanda": safe_decimal(comanda.valor_final_comanda),
        "valor_pago": safe_decimal(comanda.valor_pago),
        "valor_fiado": safe_decimal(comanda.valor_fiado),
        "valor_credito_usado": safe_decimal(comanda.valor_credito_usado),
        "observacoes": comanda.observacoes,
        "qr_code_comanda_hash": comanda.qr_code_comanda_hash,
        "created_at": comanda.created_at,
        "updated_at": comanda.updated_at,
    }

    # ✅ CORRIGIDO: Adicionar relacionamentos com campos específicos solicitados
    if hasattr(comanda, 'mesa') and comanda.mesa:
        comanda_dict["mesa"] = {
            "id": comanda.mesa.id,
            "numero_identificador": getattr(comanda.mesa, 'numero_identificador',
                                            getattr(comanda.mesa, 'numero', 'N/A')),  # ✅ Campo correto
            "status": getattr(comanda.mesa, 'status', 'Disponível'),  # ✅ Status da mesa
            "capacidade": getattr(comanda.mesa, 'capacidade', None),
            "descricao": getattr(comanda.mesa, 'descricao', None),
        }

    if hasattr(comanda, 'cliente') and comanda.cliente:
        comanda_dict["cliente"] = {
            "id": comanda.cliente.id,
            "nome": getattr(comanda.cliente, 'nome', 'N/A'),
            "imagem_url": getattr(comanda.cliente, 'imagem_url', None),  # ✅ URL da imagem
            "saldo_credito": safe_decimal(getattr(comanda.cliente, 'saldo_credito', None)),  # ✅ Saldo de crédito
            "telefone": getattr(comanda.cliente, 'telefone', None),
            "email": getattr(comanda.cliente, 'email', None),
            "cpf": getattr(comanda.cliente, 'cpf', None),
        }

    # ✅ CORRIGIDO: Serializar itens_pedido com todos os campos obrigatórios
    if hasattr(comanda, 'itens_pedido') and comanda.itens_pedido:
        comanda_dict["itens_pedido"] = []
        for item in comanda.itens_pedido:
            item_dict = {
                "id": item.id,
                "nome_item": getattr(getattr(item, 'produto', None), 'nome', 'Item sem nome'),
                "quantidade": getattr(item, 'quantidade', 1),
                "valor_unitario": safe_decimal(getattr(item, 'valor_unitario', getattr(item, 'preco_unitario', 0))),
                # ✅ Campo obrigatório
                "valor_total": safe_decimal(getattr(item, 'valor_total', 0)),  # ✅ Campo obrigatório
                "id_comanda": getattr(item, 'id_comanda', None),
                "id_produto": getattr(item, 'id_produto', None),
                "observacoes": getattr(item, 'observacoes', None),
            }
            comanda_dict["itens_pedido"].append(item_dict)
    else:
        comanda_dict["itens_pedido"] = []

    # ✅ CORRIGIDO: Serializar pagamentos com campo de data correto
    if hasattr(comanda, 'pagamentos') and comanda.pagamentos:
        comanda_dict["pagamentos"] = []
        for pagamento in comanda.pagamentos:
            # ✅ CORRIGIDO: Usar data_pagamento em vez de created_at
            data_pagamento = getattr(pagamento, 'data_pagamento', None)
            if not data_pagamento:
                # Fallback para created_at se data_pagamento não existir
                data_pagamento = getattr(pagamento, 'created_at', datetime.now())

            pagamento_dict = {
                "id": pagamento.id,
                "valor_pago": safe_decimal(pagamento.valor_pago),
                "metodo_pagamento": getattr(pagamento, 'metodo_pagamento', 'N/A'),
                "data_pagamento": data_pagamento,
                "id_comanda": getattr(pagamento, 'id_comanda', None),
                "id_cliente": getattr(pagamento, 'id_cliente', None),
                "observacoes": getattr(pagamento, 'observacoes', None),
            }
            comanda_dict["pagamentos"].append(pagamento_dict)
    else:
        comanda_dict["pagamentos"] = []

    # ✅ CORRIGIDO: Serializar fiados
    if hasattr(comanda, 'fiados_registrados') and comanda.fiados_registrados:
        comanda_dict["fiados_registrados"] = []
        for fiado in comanda.fiados_registrados:
            # ✅ CORRIGIDO: Usar data_registro em vez de created_at
            data_registro = getattr(fiado, 'data_registro', None)
            if not data_registro:
                # Fallback para created_at se data_registro não existir
                data_registro = getattr(fiado, 'created_at', datetime.now())

            fiado_dict = {
                "id": fiado.id,
                "valor_original": safe_decimal(fiado.valor_original),
                "valor_devido": safe_decimal(fiado.valor_devido),
                "data_registro": data_registro,
                "data_vencimento": getattr(fiado, 'data_vencimento', None),
                "id_comanda": getattr(fiado, 'id_comanda', None),
                "id_cliente": getattr(fiado, 'id_cliente', None),
                "observacoes": getattr(fiado, 'observacoes', None),
            }
            comanda_dict["fiados_registrados"].append(fiado_dict)
    else:
        comanda_dict["fiados_registrados"] = []

    return comanda_dict


@router.post("/", response_model=ComandaCreateResponse, status_code=status.HTTP_201_CREATED)
async def criar_comanda(
        data: ComandaCreate,
        db_session: AsyncSession = Depends(get_db)
):
    """Cria uma nova comanda."""
    try:
        comanda_criada = await ComandaService.criar_comanda(db_session, data)

        # ✅ CORRIGIDO: Usar serialização segura
        comanda_dict = _serializar_comanda_segura(comanda_criada)

        # ✅ GARANTIR que mesa sempre esteja presente
        if not comanda_dict.get("mesa"):
            # Buscar mesa separadamente se não foi carregada
            mesa = await ComandaService._buscar_mesa(db_session, comanda_criada.id_mesa)
            if mesa:
                comanda_dict["mesa"] = {
                    "id": mesa.id,
                    "numero_identificador": getattr(mesa, 'numero_identificador', getattr(mesa, 'numero', 'N/A')),
                    "status": getattr(mesa, 'status', 'Disponível'),
                    "capacidade": getattr(mesa, 'capacidade', None),
                    "descricao": getattr(mesa, 'descricao', None),
                }

        # ✅ GARANTIR que cliente esteja presente se associado
        if comanda_criada.id_cliente_associado and not comanda_dict.get("cliente"):
            cliente = await ComandaService._buscar_cliente(db_session, comanda_criada.id_cliente_associado)
            if cliente:
                comanda_dict["cliente"] = {
                    "id": cliente.id,
                    "nome": getattr(cliente, 'nome', 'N/A'),
                    "imagem_url": getattr(cliente, 'imagem_url', None),
                    "saldo_credito": Decimal(str(getattr(cliente, 'saldo_credito', 0) or 0)),
                    "telefone": getattr(cliente, 'telefone', None),
                    "email": getattr(cliente, 'email', None),
                    "cpf": getattr(cliente, 'cpf', None),
                }

        return ComandaCreateResponse(**comanda_dict)

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

        # ✅ CORRIGIDO: Usar serialização segura
        comanda_dict = _serializar_comanda_segura(comanda)
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

        # ✅ CORRIGIDO: Serializar cada comanda de forma segura
        comandas_serializadas = []
        for comanda in comandas:
            comanda_dict = _serializar_comanda_segura(comanda)
            comandas_serializadas.append(ComandaInResponse(**comanda_dict))

        return comandas_serializadas
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

        # ✅ CORRIGIDO: Usar serialização segura
        comanda_dict = _serializar_comanda_segura(comanda_ativa)
        return ComandaInResponse(**comanda_dict)

    except ComandaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar comanda ativa da mesa {mesa_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")


# @router.post("/{comanda_id}/registrar-pagamento", response_model=ComandaInResponse)
# async def registrar_pagamento(
#         comanda_id: int,
#         pagamento_data: PagamentoCreateSchema = Body(...),
#         db_session: AsyncSession = Depends(get_db)
# ):
#     """Registra um pagamento na comanda"""
#     try:
#         comanda_atualizada = await ComandaService.registrar_pagamento(db_session, comanda_id, pagamento_data)
#
#         # ✅ CORRIGIDO: Usar serialização segura
#         comanda_dict = _serializar_comanda_segura(comanda_atualizada)
#         return ComandaInResponse(**comanda_dict)
#
#     except ComandaValidationError as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
#     except Exception as e:
#         logger.error(f"❌ Erro ao registrar pagamento na comanda {comanda_id}: {e}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")


# @router.post("/{comanda_id}/registrar-fiado", response_model=ComandaInResponse)
# async def registrar_fiado(
#         comanda_id: int,
#         fiado_data: FiadoCreate = Body(...),
#         db_session: AsyncSession = Depends(get_db)
# ):
#     """Registra o saldo da comanda como fiado para o cliente"""
#     try:
#         comanda_atualizada = await ComandaService.registrar_fiado(db_session, comanda_id, fiado_data)
#
#         # ✅ CORRIGIDO: Usar serialização segura
#         comanda_dict = _serializar_comanda_segura(comanda_atualizada)
#         return ComandaInResponse(**comanda_dict)
#
#     except ComandaValidationError as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
#     except Exception as e:
#         logger.error(f"❌ Erro ao registrar fiado na comanda {comanda_id}: {e}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")


@router.post("/{comanda_id}/fechar", response_model=ComandaInResponse)
async def fechar_comanda(
        comanda_id: int,
        db_session: AsyncSession = Depends(get_db)
):
    """
    Fecha a comanda com as seguintes regras:
    - Se a comanda estiver vazia (sem itens, pagamentos), pode ser fechada
    - Se tiver itens, deve estar totalmente paga ou com saldo em fiado
    """
    try:
        logger.info(f"🔒 Tentando fechar comanda {comanda_id}")

        comanda_fechada = await ComandaService.fechar_comanda(db_session, comanda_id)

        # ✅ CORRIGIDO: Usar serialização segura
        comanda_dict = _serializar_comanda_segura(comanda_fechada)

        logger.info(f"✅ Comanda {comanda_id} fechada com sucesso")
        return ComandaInResponse(**comanda_dict)

    except ComandaValidationError as e:
        logger.warning(f"⚠️ Erro de validação ao fechar comanda {comanda_id}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erro inesperado ao fechar comanda {comanda_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Erro interno do servidor ao fechar comanda")


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
        db_session: AsyncSession = Depends(get_db)):
    """Endpoint para forçar recálculo dos totais da comanda"""

    try:
        logger.info(f"🔄 Iniciando recálculo da comanda {comanda_id}")

        # ✅ VERIFICAR SE A COMANDA EXISTE PRIMEIRO
        comanda_existe = await ComandaService.buscar_comanda_por_id(db_session, comanda_id)
        if not comanda_existe:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comanda não encontrada")

        # ✅ FAZER O RECÁLCULO
        comanda_atualizada = await ComandaService.recalcular_totais_comanda(db_session, comanda_id, fazer_commit=True)
        if not comanda_atualizada:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Erro ao recalcular totais da comanda")

        # ✅ SERIALIZAR RESPOSTA
        comanda_dict = _serializar_comanda_segura(comanda_atualizada)

        logger.info(f"✅ Recálculo concluído para comanda {comanda_id}")
        return ComandaInResponse(**comanda_dict)

    except HTTPException:
        raise
    except ComandaValidationError as e:
        logger.warning(f"⚠️ Erro de validação no recálculo da comanda {comanda_id}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erro inesperado ao recalcular totais da comanda {comanda_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Erro interno do servidor ao recalcular totais")
