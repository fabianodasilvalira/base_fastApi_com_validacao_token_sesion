from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.dialects.postgresql import Any
from sqlalchemy.orm import Session
from datetime import date
from app import schemas
from app.api import deps
from app.schemas.relatorio_schemas import RelatorioFiadoSchemas, RelatorioVendasSchemas, \
    RelatorioProdutosVendidosSchemas, RelatorioPedidosPorStatusSchemas, RelatorioPedidosPorUsuarioSchemas
from app.services.relatorio_service import (
    get_relatorio_fiado,
    get_relatorio_vendas,
    get_relatorio_produtos_mais_vendidos,
    get_relatorio_pedidos_por_status,
    get_relatorio_pedidos_por_usuario
)

router = APIRouter()

# Relatório de Fiados
@router.get("/fiado", response_model=RelatorioFiadoSchemas)
def get_relatorio_fiado_endpoint(
        data_inicio: date,
        data_fim: date,
        db: Session = Depends(deps.get_db_session)
) -> Any:
    if data_inicio > data_fim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data de início não pode ser posterior à data de fim."
        )

    try:
        relatorio = get_relatorio_fiado(db=db, data_inicio=data_inicio, data_fim=data_fim)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao gerar o relatório de fiado: {e}"
        )

    return relatorio

# Relatório de Vendas
@router.get("/vendas", response_model=RelatorioVendasSchemas)
def get_relatorio_vendas_endpoint(
        data_inicio: date,
        data_fim: date,
        db: Session = Depends(deps.get_db_session)
) -> Any:
    if data_inicio > data_fim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data de início não pode ser posterior à data de fim."
        )

    try:
        relatorio = get_relatorio_vendas(db=db, data_inicio=data_inicio, data_fim=data_fim)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao gerar o relatório de vendas: {e}"
        )

    return relatorio

# Relatório de Produtos Mais Vendidos
@router.get("/produtos-mais-vendidos", response_model=RelatorioProdutosVendidosSchemas)
def get_relatorio_produtos_mais_vendidos_endpoint(
        data_inicio: date,
        data_fim: date,
        db: Session = Depends(deps.get_db_session)
) -> Any:
    if data_inicio > data_fim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data de início não pode ser posterior à data de fim."
        )

    try:
        relatorio = get_relatorio_produtos_mais_vendidos(db=db, data_inicio=data_inicio, data_fim=data_fim)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao gerar o relatório de produtos mais vendidos: {e}"
        )

    return relatorio

# Relatório de Pedidos por Status
@router.get("/pedidos-status", response_model=RelatorioPedidosPorStatusSchemas)
def get_relatorio_pedidos_por_status_endpoint(
        status_pedido: str,
        data_inicio: date,
        data_fim: date,
        db: Session = Depends(deps.get_db_session)
) -> Any:
    if data_inicio > data_fim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data de início não pode ser posterior à data de fim."
        )

    try:
        relatorio = get_relatorio_pedidos_por_status(db=db, status_pedido=status_pedido, data_inicio=data_inicio, data_fim=data_fim)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao gerar o relatório de pedidos por status: {e}"
        )

    return relatorio

# Relatório de Pedidos por Usuário
@router.get("/pedidos-usuario", response_model=RelatorioPedidosPorUsuarioSchemas)
def get_relatorio_pedidos_por_usuario_endpoint(
        usuario_id: int,
        data_inicio: date,
        data_fim: date,
        db: Session = Depends(deps.get_db_session)
) -> Any:
    if data_inicio > data_fim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data de início não pode ser posterior à data de fim."
        )

    try:
        relatorio = get_relatorio_pedidos_por_usuario(db=db, usuario_id=usuario_id, data_inicio=data_inicio, data_fim=data_fim)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao gerar o relatório de pedidos por usuário: {e}"
        )

    return relatorio
