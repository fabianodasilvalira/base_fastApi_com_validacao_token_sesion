from typing import List
from pydantic import BaseModel
from datetime import date

# Relatório de Fiados
class FiadoSchemas(BaseModel):
    id: int
    nome_cliente: str
    valor_total: float
    status: str
    data_criacao: date

class RelatorioFiadoSchemas(BaseModel):
    fiados: List[FiadoSchemas]

# Relatório de Vendas
class VendaSchemas(BaseModel):
    id: int
    valor_total: float
    data_venda: date

class RelatorioVendasSchemas(BaseModel):
    vendas: List[VendaSchemas]

# Relatório de Produtos Vendidos
class ProdutoVendidoSchemas(BaseModel):
    id: int
    nome_produto: str
    quantidade_vendida: int
    preco_unitario: float
    preco_total: float

class RelatorioProdutosVendidosSchemas(BaseModel):
    produtos_vendidos: List[ProdutoVendidoSchemas]

# Relatório de Pedidos por Status
class PedidoStatusSchemas(BaseModel):
    id: int
    status: str
    data_criacao: date
    valor_total: float

class RelatorioPedidosPorStatusSchemas(BaseModel):
    pedidos: List[PedidoStatusSchemas]

# Relatório de Pedidos por Usuário
class PedidoDetalhadoSchemas(BaseModel):
    id: int
    status: str
    data_criacao: date
    total: float
    produtos: List[ProdutoVendidoSchemas]

class RelatorioPedidosPorUsuarioSchemas(BaseModel):
    usuario_id: int
    nome_usuario: str
    pedidos: List[PedidoDetalhadoSchemas]
