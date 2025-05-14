from sqlalchemy.orm import Session
from app.models.pedido import Pedido, ItemPedido
from app.schemas.pedido_schemas import PedidoCreate


# Função para criar um novo pedido
def criar_pedido(db: Session, pedido_dados: PedidoCreate) -> Pedido:
    novo_pedido = Pedido(
        id_comanda=pedido_dados.id_comanda,
        id_usuario_registrou=pedido_dados.id_usuario_registrou,
        tipo_pedido=pedido_dados.tipo_pedido,
        status_geral_pedido=pedido_dados.status_geral_pedido,
        observacoes_pedido=pedido_dados.observacoes_pedido,
        itens=[  # Criação dos itens do pedido
            ItemPedido(
                id_produto=item.id_produto,
                quantidade=item.quantidade,
                preco_unitario_no_momento=item.preco_unitario_no_momento,
                preco_total_item=item.preco_total_item,
                observacoes_item=item.observacoes_item,
                status_item_pedido=item.status_item_pedido
            ) for item in pedido_dados.itens
        ]
    )

    db.add(novo_pedido)
    db.commit()
    db.refresh(novo_pedido)
    return novo_pedido


# Função para listar os pedidos
def listar_pedidos(db: Session):
    return db.query(Pedido).all()  # Retorna uma lista vazia em vez de None, se não houver pedidos
