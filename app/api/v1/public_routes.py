# app/api/v1/public_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.core.session import get_db_session
from app.services import produto_service, mesa_service, comanda_service # Supondo que estes services existem/serão criados
from app.schemas.produto_schemas import ProdutoOut # Reutilizando schema existente
from app.schemas.comanda_schemas import ComandaInResponse # Para detalhes da comanda
from app.schemas.mesa_schemas import MesaOut # Para detalhes da mesa

# TODO: Definir schemas específicos para respostas públicas se necessário, para não expor dados internos.

router = APIRouter(prefix="/public", tags=["Public Access"])

@router.get("/cardapio", response_model=List[ProdutoOut])
async def get_public_cardapio(
    db: AsyncSession = Depends(get_db_session)
):
    """
    Retorna o cardápio público com todos os produtos disponíveis.
    """
    produtos = await produto_service.listar_produtos_disponiveis(db) # Supõe um novo método ou ajuste no existente
    if not produtos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cardápio não encontrado ou vazio.")
    return produtos

@router.get("/mesa/{qr_code_hash}/cardapio", response_model=List[ProdutoOut])
async def get_cardapio_via_mesa_qr(
    qr_code_hash: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Retorna o cardápio ao acessar via QRCode de uma mesa específica.
    Valida se o qr_code_hash da mesa é válido.
    """
    mesa = await mesa_service.get_mesa_by_qr_code_hash(db, qr_code_hash) # Novo service method
    if not mesa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QRCode da mesa inválido ou mesa não encontrada.")
    if not mesa.ativa_para_pedidos:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Esta mesa não está ativa para pedidos no momento.")
        
    # A lógica do cardápio é a mesma do cardápio público geral
    produtos = await produto_service.listar_produtos_disponiveis(db)
    if not produtos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cardápio não encontrado ou vazio.")
    return produtos

@router.get("/mesa/{qr_code_hash}/comanda", response_model=ComandaInResponse) # Pode precisar de um schema público mais restrito
async def get_comanda_via_mesa_qr(
    qr_code_hash: str, 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Permite ao cliente visualizar sua comanda ativa através do QRCode da mesa.
    """
    mesa = await mesa_service.get_mesa_by_qr_code_hash(db, qr_code_hash)
    if not mesa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QRCode da mesa inválido ou mesa não encontrada.")

    comanda_ativa = await comanda_service.get_active_comanda_by_mesa_id(db, mesa.id) # Novo service method
    if not comanda_ativa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma comanda ativa encontrada para esta mesa.")
    
    # Verificar se o qr_code_comanda_hash da comanda corresponde ou se a lógica de acesso é só pela mesa
    # Para simplificar, se a mesa tem QR e tem comanda ativa, mostramos.
    # Em um cenário mais seguro, o QR da mesa poderia levar a um QR específico da comanda.
    return comanda_ativa

@router.post("/mesa/{qr_code_hash}/chamar-garcom", status_code=status.HTTP_200_OK)
async def chamar_garcom_via_mesa_qr(
    qr_code_hash: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Permite ao cliente chamar um garçom através do QRCode da mesa.
    (Implementação inicial, notificação real via WebSocket/Redis será na etapa 006)
    """
    mesa = await mesa_service.get_mesa_by_qr_code_hash(db, qr_code_hash)
    if not mesa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QRCode da mesa inválido ou mesa não encontrada.")

    # Lógica de notificação (ex: publicar em um canal Redis) será adicionada depois.
    # Por agora, apenas log ou confirmação.
    print(f"Chamada para garçom recebida da mesa {mesa.numero_identificador} (QR: {qr_code_hash})")
    return {"message": f"Garçom chamado para a mesa {mesa.numero_identificador}. Aguarde um momento."}





from app.schemas.public_pedido_schemas import PedidoPublicCreateSchema, PedidoPublicResponseSchema # Adicionado
from app.services import pedido_service # Adicionado para o novo fluxo

@router.post("/mesa/{qr_code_hash}/fazer-pedido", response_model=PedidoPublicResponseSchema, status_code=status.HTTP_201_CREATED)
async def fazer_pedido_via_mesa_qr(
    qr_code_hash: str,
    pedido_data: PedidoPublicCreateSchema,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Permite ao cliente fazer um novo pedido ou adicionar itens a uma comanda existente
    através do QRCode da mesa.
    """
    mesa = await mesa_service.get_mesa_by_qr_code_hash(db, qr_code_hash)
    if not mesa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QRCode da mesa inválido ou mesa não encontrada.")
    
    if not mesa.ativa_para_pedidos:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Esta mesa não está ativa para receber pedidos no momento.")

    # A lógica de encontrar/criar comanda e adicionar itens será tratada no serviço
    try:
        comanda_atualizada_info = await pedido_service.processar_pedido_publico(
            db=db, 
            mesa_id=mesa.id, 
            pedido_public_data=pedido_data,
            mesa_numero=mesa.numero_identificador # Passando o número da mesa para a resposta
        )
        return comanda_atualizada_info
    except HTTPException as http_exc: # Repassar HTTPExceptions do service
        raise http_exc
    except Exception as e:
        # Logar o erro e retornar um erro genérico
        # logger.error(f"Erro ao processar pedido público para mesa {mesa.id} (QR: {qr_code_hash}): {e}")
        print(f"Erro ao processar pedido público para mesa {mesa.id} (QR: {qr_code_hash}): {e}") # Log temporário
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ocorreu um erro ao processar seu pedido. Tente novamente mais tarde.")

