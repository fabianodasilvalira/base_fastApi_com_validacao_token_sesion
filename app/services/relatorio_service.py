from sqlalchemy.orm import Session
from datetime import date
from app.models.fiado import Fiado  # Ajuste conforme seu modelo de Fiado
from app.models.venda import Venda  # Ajuste conforme seu modelo de Venda
from app.models.produto import Produto  # Ajuste conforme seu modelo de Produto
from app.models.pedido import Pedido  # Ajuste conforme seu modelo de Pedido
from app.schemas.relatorio_schemas import (
    RelatorioFiadoSchemas,
    RelatorioVendasSchemas,
    RelatorioProdutosVendidosSchemas,
    RelatorioPedidosPorStatusSchemas,
    RelatorioPedidosPorUsuarioSchemas, ProdutoVendidoSchemas, PedidoDetalhadoSchemas, PedidoStatusSchemas, VendaSchemas,
    FiadoSchemas,
)

# Serviço para Relatório de Fiados
def get_relatorio_fiado(db: Session, data_inicio: date, data_fim: date) -> RelatorioFiadoSchemas:
    fiados_query = db.query(Fiado).filter(
        Fiado.status.in_(['Pendente', 'Pago Parcialmente']),
        Fiado.data_criacao <= data_fim
    ).all()

    fiados = [
        FiadoSchemas(
            id=fiado.id,
            nome_cliente=fiado.nome_cliente,
            valor_total=fiado.valor_total,
            status=fiado.status,
            data_criacao=fiado.data_criacao
        )
        for fiado in fiados_query
    ]

    return RelatorioFiadoSchemas(fiados=fiados)

# Serviço para Relatório de Vendas
def get_relatorio_vendas(db: Session, data_inicio: date, data_fim: date) -> RelatorioVendasSchemas:
    vendas_query = db.query(Venda).filter(
        Venda.data_venda >= data_inicio,
        Venda.data_venda <= data_fim
    ).all()

    vendas = [
        VendaSchemas(
            id=venda.id,
            valor_total=venda.valor_total,
            data_venda=venda.data_venda
        )
        for venda in vendas_query
    ]

    return RelatorioVendasSchemas(vendas=vendas)

# Serviço para Relatório de Produtos Mais Vendidos
def get_relatorio_produtos_mais_vendidos(db: Session, data_inicio: date, data_fim: date) -> RelatorioProdutosVendidosSchemas:
    produtos_query = db.query(Produto).filter(
        Produto.data_venda >= data_inicio,
        Produto.data_venda <= data_fim
    ).all()

    produtos_vendidos = [
        ProdutoVendidoSchemas(
            id=produto.id,
            nome_produto=produto.nome,
            quantidade_vendida=produto.quantidade_vendida,
            preco_unitario=produto.preco_unitario,
            preco_total=produto.preco_vendido
        )
        for produto in produtos_query
    ]

    return RelatorioProdutosVendidosSchemas(produtos_vendidos=produtos_vendidos)

# Serviço para Relatório de Pedidos por Status
def get_relatorio_pedidos_por_status(db: Session, status_pedido: str, data_inicio: date, data_fim: date) -> RelatorioPedidosPorStatusSchemas:
    pedidos_query = db.query(Pedido).filter(
        Pedido.status == status_pedido,
        Pedido.data_criacao >= data_inicio,
        Pedido.data_criacao <= data_fim
    ).all()

    pedidos = [
        PedidoStatusSchemas(
            id=pedido.id,
            status=pedido.status,
            data_criacao=pedido.data_criacao,
            valor_total=pedido.valor_total
        )
        for pedido in pedidos_query
    ]

    return RelatorioPedidosPorStatusSchemas(pedidos=pedidos)

# Serviço para Relatório de Pedidos por Usuário
def get_relatorio_pedidos_por_usuario(db: Session, usuario_id: int, data_inicio: date, data_fim: date) -> RelatorioPedidosPorUsuarioSchemas:
    pedidos_query = db.query(Pedido).filter(
        Pedido.usuario_id == usuario_id,
        Pedido.data_criacao >= data_inicio,
        Pedido.data_criacao <= data_fim
    ).all()

    pedidos_detalhados = []

    for pedido in pedidos_query:
        produtos_query = db.query(Produto).filter(Produto.pedido_id == pedido.id).all()

        produtos_detalhados = [
            ProdutoVendidoSchemas(
                id=produto.id,
                nome_produto=produto.nome,
                quantidade_vendida=produto.quantidade_vendida,
                preco_unitario=produto.preco_unitario,
                preco_total=produto.preco_unitario * produto.quantidade_vendida
            )
            for produto in produtos_query
        ]

        pedidos_detalhados.append(
            PedidoDetalhadoSchemas(
                id=pedido.id,
                status=pedido.status,
                data_criacao=pedido.data_criacao,
                total=pedido.valor_total,
                produtos=produtos_detalhados
            )
        )

    return RelatorioPedidosPorUsuarioSchemas(
        usuario_id=usuario_id,
        nome_usuario="Nome do Usuário",  # Ajuste para pegar o nome real do usuário
        pedidos=pedidos_detalhados
    )
