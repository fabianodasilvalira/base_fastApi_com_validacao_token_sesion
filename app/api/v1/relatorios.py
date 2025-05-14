# app/api/v1/relatorios.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession # Alterado para AsyncSession
from datetime import date, timedelta
from typing import Optional, Any, Literal # Adicionado Literal

from app.core.session import get_db_session # Ajustado para o novo get_db_session async
from app.schemas.relatorio_schemas import (
    RelatorioFiadoSchemas, RelatorioVendasSchemas,
    RelatorioProdutosVendidosSchemas, RelatorioPedidosPorStatusSchemas, 
    RelatorioPedidosPorUsuarioSchemas
)
from app.services import relatorio_service # Assumindo que o service será ajustado para async

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])

# Função auxiliar para determinar datas com base no período
def get_date_range_from_period(periodo: Optional[Literal["hoje", "semanal", "mensal", "anual"]],
                               data_inicio: Optional[date],
                               data_fim: Optional[date]) -> tuple[date, date]:
    today = date.today()
    if periodo == "hoje":
        return today, today
    elif periodo == "semanal":
        start_of_week = today - timedelta(days=today.weekday())
        return start_of_week, today
    elif periodo == "mensal":
        start_of_month = today.replace(day=1)
        return start_of_month, today
    elif periodo == "anual":
        start_of_year = today.replace(month=1, day=1)
        return start_of_year, today
    elif data_inicio and data_fim:
        if data_inicio > data_fim:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A data de início não pode ser posterior à data de fim."
            )
        return data_inicio, data_fim
    else:
        # Default para o mês atual se nenhum período ou datas específicas forem fornecidos
        # Ou pode levantar um erro se datas explícitas forem preferidas quando não há período
        start_of_month = today.replace(day=1)
        return start_of_month, today

@router.get("/fiado", response_model=RelatorioFiadoSchemas)
async def get_relatorio_fiado_endpoint(
    periodo: Optional[Literal["hoje", "semanal", "mensal", "anual"]] = Query(None, description="Período predefinido para o relatório (hoje, semanal, mensal, anual). Sobrepõe data_inicio e data_fim se fornecido."),
    data_inicio: Optional[date] = Query(None, description="Data de início (YYYY-MM-DD) para o período do relatório, usado se 'periodo' não for fornecido."),
    data_fim: Optional[date] = Query(None, description="Data de fim (YYYY-MM-DD) para o período do relatório, usado se 'periodo' não for fornecido."),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    
    start_date, end_date = get_date_range_from_period(periodo, data_inicio, data_fim)

    try:
        relatorio = await relatorio_service.get_relatorio_fiado(db=db, data_inicio=start_date, data_fim=end_date)
    except Exception as e:
        # Logar o erro e retornar uma mensagem genérica ou mais específica se seguro
        # logger.error(f"Erro ao gerar relatório de fiado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao gerar o relatório de fiado: {str(e)}"
        )
    return relatorio

@router.get("/vendas", response_model=RelatorioVendasSchemas)
async def get_relatorio_vendas_endpoint(
    periodo: Optional[Literal["hoje", "semanal", "mensal", "anual"]] = Query(None, description="Período predefinido para o relatório."),
    data_inicio: Optional[date] = Query(None, description="Data de início (YYYY-MM-DD)."),
    data_fim: Optional[date] = Query(None, description="Data de fim (YYYY-MM-DD)."),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    start_date, end_date = get_date_range_from_period(periodo, data_inicio, data_fim)
    try:
        relatorio = await relatorio_service.get_relatorio_vendas(db=db, data_inicio=start_date, data_fim=end_date)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao gerar o relatório de vendas: {str(e)}"
        )
    return relatorio

@router.get("/produtos-mais-vendidos", response_model=RelatorioProdutosVendidosSchemas)
async def get_relatorio_produtos_mais_vendidos_endpoint(
    periodo: Optional[Literal["hoje", "semanal", "mensal", "anual"]] = Query(None, description="Período predefinido para o relatório."),
    data_inicio: Optional[date] = Query(None, description="Data de início (YYYY-MM-DD)."),
    data_fim: Optional[date] = Query(None, description="Data de fim (YYYY-MM-DD)."),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    start_date, end_date = get_date_range_from_period(periodo, data_inicio, data_fim)
    try:
        relatorio = await relatorio_service.get_relatorio_produtos_mais_vendidos(db=db, data_inicio=start_date, data_fim=end_date)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao gerar o relatório de produtos mais vendidos: {str(e)}"
        )
    return relatorio

@router.get("/pedidos-status", response_model=RelatorioPedidosPorStatusSchemas)
async def get_relatorio_pedidos_por_status_endpoint(
    status_pedido: str,
    periodo: Optional[Literal["hoje", "semanal", "mensal", "anual"]] = Query(None, description="Período predefinido para o relatório."),
    data_inicio: Optional[date] = Query(None, description="Data de início (YYYY-MM-DD)."),
    data_fim: Optional[date] = Query(None, description="Data de fim (YYYY-MM-DD)."),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    start_date, end_date = get_date_range_from_period(periodo, data_inicio, data_fim)
    try:
        relatorio = await relatorio_service.get_relatorio_pedidos_por_status(db=db, status_pedido=status_pedido, data_inicio=start_date, data_fim=end_date)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao gerar o relatório de pedidos por status: {str(e)}"
        )
    return relatorio

@router.get("/pedidos-usuario", response_model=RelatorioPedidosPorUsuarioSchemas)
async def get_relatorio_pedidos_por_usuario_endpoint(
    usuario_id: int,
    periodo: Optional[Literal["hoje", "semanal", "mensal", "anual"]] = Query(None, description="Período predefinido para o relatório."),
    data_inicio: Optional[date] = Query(None, description="Data de início (YYYY-MM-DD)."),
    data_fim: Optional[date] = Query(None, description="Data de fim (YYYY-MM-DD)."),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    start_date, end_date = get_date_range_from_period(periodo, data_inicio, data_fim)
    try:
        relatorio = await relatorio_service.get_relatorio_pedidos_por_usuario(db=db, usuario_id=usuario_id, data_inicio=start_date, data_fim=end_date)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao gerar o relatório de pedidos por usuário: {str(e)}"
        )
    return relatorio

