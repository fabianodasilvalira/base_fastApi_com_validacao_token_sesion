from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app import schemas, services
from app.core.session import get_db_session
from uuid import UUID

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

# Criação de um novo pedido
@router.post("/", response_model=schemas.Pedido, status_code=status.HTTP_201_CREATED)
async def criar(pedido: schemas.PedidoCreate, db: Session = Depends(get_db_session)):
    return services.criar_pedido(db, pedido)

# Listar pedidos (com filtros opcionais)
@router.get("/", response_model=List[schemas.Pedido])
async def listar(
    db: Session = Depends(get_db_session),
    status: Optional[str] = None,  # Exemplo de filtro por status
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None
):
    return services.listar_pedidos(db, status=status, data_inicio=data_inicio, data_fim=data_fim)

# Atualização do status do pedido
@router.put("/{pedido_id}/status", response_model=schemas.Pedido)
async def atualizar_status_pedido(
    pedido_id: UUID,
    status_update: schemas.StatusPedido,
    db: Session = Depends(get_db_session)
):
    pedido_service = services.PedidoService()
    pedido, mensagem = await pedido_service.atualizar_status_pedido(db, pedido_id, status_update)

    if pedido is None:
        raise HTTPException(status_code=400, detail=mensagem)

    return pedido

# Detalhar um pedido específico
@router.get("/{pedido_id}", response_model=schemas.Pedido)
async def detalhar_pedido(pedido_id: UUID, db: Session = Depends(get_db_session)):
    pedido = services.buscar_pedido(db, pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return pedido

# Adicionar item ao pedido
@router.post("/{pedido_id}/itens/", response_model=schemas.ItemPedido)
async def adicionar_item_pedido(
    pedido_id: UUID, item_in: schemas.ItemPedidoCreate, db: Session = Depends(get_db_session)
):
    item = services.adicionar_item(db, pedido_id, item_in)
    if not item:
        raise HTTPException(status_code=400, detail="Erro ao adicionar item ao pedido")
    return item

# Remover item do pedido
@router.delete("/{pedido_id}/itens/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_item_pedido(
    pedido_id: UUID, item_id: int, db: Session = Depends(get_db_session)
):
    sucesso = services.remover_item(db, pedido_id, item_id)
    if not sucesso:
        raise HTTPException(status_code=400, detail="Erro ao remover item do pedido")
    return {"detail": "Item removido com sucesso"}

# Cancelar pedido
@router.put("/{pedido_id}/cancelar", response_model=schemas.Pedido)
async def cancelar_pedido(
    pedido_id: UUID, db: Session = Depends(get_db_session)
):
    pedido = services.cancelar_pedido(db, pedido_id)
    if not pedido:
        raise HTTPException(status_code=400, detail="Erro ao cancelar o pedido")
    return pedido

# Listar pedidos de um usuário específico
@router.get("/usuario/{usuario_id}", response_model=List[schemas.Pedido])
async def listar_pedidos_usuario(
    usuario_id: int, db: Session = Depends(get_db_session)
):
    pedidos = services.listar_pedidos_por_usuario(db, usuario_id)
    return pedidos
