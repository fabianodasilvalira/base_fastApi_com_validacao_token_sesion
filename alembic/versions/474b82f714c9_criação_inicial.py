"""Criação inicial

Revision ID: 474b82f714c9
Revises: 
Create Date: 2025-06-11 10:40:43.651740

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '474b82f714c9'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('categorias',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('nome', sa.String(length=100), nullable=False),
    sa.Column('descricao', sa.Text(), nullable=True),
    sa.Column('imagem_url', sa.String(length=255), nullable=True),
    sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('atualizado_em', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_categorias_id'), 'categorias', ['id'], unique=False)
    op.create_index(op.f('ix_categorias_nome'), 'categorias', ['nome'], unique=True)
    op.create_table('clientes',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('nome', sa.String(), nullable=False),
    sa.Column('telefone', sa.String(), nullable=False),
    sa.Column('observacoes', sa.Text(), nullable=True),
    sa.Column('endereco', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('imagem_url', sa.String(length=255), nullable=True),
    sa.Column('saldo_credito', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clientes_id'), 'clientes', ['id'], unique=False)
    op.create_index(op.f('ix_clientes_imagem_url'), 'clientes', ['imagem_url'], unique=False)
    op.create_index(op.f('ix_clientes_nome'), 'clientes', ['nome'], unique=False)
    op.create_index(op.f('ix_clientes_telefone'), 'clientes', ['telefone'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('first_name', sa.String(), nullable=True),
    sa.Column('last_name', sa.String(), nullable=True),
    sa.Column('phone', sa.String(), nullable=True),
    sa.Column('imagem_url', sa.String(length=255), nullable=True),
    sa.Column('is_verified', sa.Boolean(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_superuser', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('phone')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_imagem_url'), 'users', ['imagem_url'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('mesas',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('numero_identificador', sa.String(), nullable=False),
    sa.Column('capacidade', sa.Integer(), nullable=True),
    sa.Column('status', sa.Enum('DISPONIVEL', 'OCUPADA', 'RESERVADA', 'FECHADA', 'MANUTENCAO', name='statusmesa'), nullable=False),
    sa.Column('qr_code_hash', sa.String(), nullable=True),
    sa.Column('id_cliente_associado', sa.Integer(), nullable=True),
    sa.Column('ativa_para_pedidos', sa.Boolean(), nullable=False),
    sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('atualizado_em', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['id_cliente_associado'], ['clientes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mesas_id'), 'mesas', ['id'], unique=False)
    op.create_index(op.f('ix_mesas_numero_identificador'), 'mesas', ['numero_identificador'], unique=True)
    op.create_index(op.f('ix_mesas_qr_code_hash'), 'mesas', ['qr_code_hash'], unique=True)
    op.create_table('password_reset_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('token', sa.String(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_password_reset_tokens_id'), 'password_reset_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_password_reset_tokens_token'), 'password_reset_tokens', ['token'], unique=True)
    op.create_table('produtos',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('nome', sa.String(), nullable=False),
    sa.Column('descricao', sa.Text(), nullable=True),
    sa.Column('preco_unitario', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('disponivel', sa.Boolean(), nullable=False),
    sa.Column('imagem_url', sa.String(length=255), nullable=True),
    sa.Column('categoria_id', sa.Integer(), nullable=True),
    sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['categoria_id'], ['categorias.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_produtos_categoria_id'), 'produtos', ['categoria_id'], unique=False)
    op.create_index(op.f('ix_produtos_id'), 'produtos', ['id'], unique=False)
    op.create_index(op.f('ix_produtos_nome'), 'produtos', ['nome'], unique=False)
    op.create_table('refresh_tokens',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('token', sa.String(), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_refresh_tokens_id'), 'refresh_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_token'), 'refresh_tokens', ['token'], unique=True)
    op.create_table('comandas',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('id_mesa', sa.Integer(), nullable=False),
    sa.Column('id_cliente_associado', sa.Integer(), nullable=True),
    sa.Column('status_comanda', sa.Enum('ABERTA', 'FECHADA', 'PAGA_PARCIALMENTE', 'PAGA_TOTALMENTE', 'CANCELADA', 'EM_FIADO', name='statuscomanda'), nullable=False),
    sa.Column('valor_total_calculado', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('percentual_taxa_servico', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('valor_taxa_servico', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('valor_desconto', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('valor_final_comanda', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('valor_pago', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('valor_fiado', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('valor_credito_usado', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('motivo_cancelamento', sa.Text(), nullable=True),
    sa.Column('observacoes', sa.Text(), nullable=True),
    sa.Column('qr_code_comanda_hash', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id_cliente_associado'], ['clientes.id'], ),
    sa.ForeignKeyConstraint(['id_mesa'], ['mesas.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comandas_id'), 'comandas', ['id'], unique=False)
    op.create_index(op.f('ix_comandas_qr_code_comanda_hash'), 'comandas', ['qr_code_comanda_hash'], unique=True)
    op.create_table('fiados',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('id_comanda', sa.Integer(), nullable=False),
    sa.Column('id_cliente', sa.Integer(), nullable=False),
    sa.Column('id_usuario_registrou', sa.Integer(), nullable=True),
    sa.Column('valor_original', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('valor_devido', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('status_fiado', sa.Enum('PENDENTE', 'PAGO_PARCIALMENTE', 'PAGO_TOTALMENTE', 'CANCELADO', name='statusfiado'), nullable=False),
    sa.Column('data_vencimento', sa.Date(), nullable=True),
    sa.Column('observacoes', sa.Text(), nullable=True),
    sa.Column('data_registro', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id_cliente'], ['clientes.id'], ),
    sa.ForeignKeyConstraint(['id_comanda'], ['comandas.id'], ),
    sa.ForeignKeyConstraint(['id_usuario_registrou'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fiados_id'), 'fiados', ['id'], unique=False)
    op.create_table('pedidos',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('id_comanda', sa.Integer(), nullable=False),
    sa.Column('id_usuario_registrou', sa.Integer(), nullable=True),
    sa.Column('mesa_id', sa.Integer(), nullable=True),
    sa.Column('tipo_pedido', sa.Enum('INTERNO_MESA', 'EXTERNO_DELIVERY', 'EXTERNO_RETIRADA', name='tipopedido'), nullable=False),
    sa.Column('status_geral_pedido', sa.Enum('RECEBIDO', 'EM_PREPARO', 'PRONTO_PARA_ENTREGA', 'ENTREGUE_NA_MESA', 'SAIU_PARA_ENTREGA_EXTERNA', 'ENTREGUE_CLIENTE_EXTERNO', 'CANCELADO', name='statuspedido'), nullable=False),
    sa.Column('observacoes_pedido', sa.Text(), nullable=True),
    sa.Column('motivo_cancelamento', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id_comanda'], ['comandas.id'], ),
    sa.ForeignKeyConstraint(['id_usuario_registrou'], ['users.id'], ),
    sa.ForeignKeyConstraint(['mesa_id'], ['mesas.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pedidos_id'), 'pedidos', ['id'], unique=False)
    op.create_table('vendas',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('valor_total', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('data_venda', sa.Date(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('cliente_id', sa.Integer(), nullable=True),
    sa.Column('comanda_id', sa.Integer(), nullable=True),
    sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('atualizado_em', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id'], ),
    sa.ForeignKeyConstraint(['comanda_id'], ['comandas.id'], ),
    sa.ForeignKeyConstraint(['usuario_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vendas_id'), 'vendas', ['id'], unique=False)
    op.create_table('itens_pedido',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('id_pedido', sa.Integer(), nullable=False),
    sa.Column('id_comanda', sa.Integer(), nullable=False),
    sa.Column('id_produto', sa.Integer(), nullable=False),
    sa.Column('quantidade', sa.Integer(), nullable=False),
    sa.Column('preco_unitario', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('preco_total', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('observacoes', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('RECEBIDO', 'PREPARANDO', 'PRONTO', 'FINALIZADO', 'CANCELADO', name='statuspedidoenum'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id_comanda'], ['comandas.id'], ),
    sa.ForeignKeyConstraint(['id_pedido'], ['pedidos.id'], ),
    sa.ForeignKeyConstraint(['id_produto'], ['produtos.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_itens_pedido_id'), 'itens_pedido', ['id'], unique=False)
    op.create_table('pagamentos',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('id_comanda', sa.Integer(), nullable=False),
    sa.Column('id_cliente', sa.Integer(), nullable=True),
    sa.Column('id_usuario_registrou', sa.Integer(), nullable=True),
    sa.Column('id_venda', sa.Integer(), nullable=True),
    sa.Column('id_pedido', sa.Integer(), nullable=True),
    sa.Column('valor_pago', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('metodo_pagamento', sa.Enum('DINHEIRO', 'CARTAO_CREDITO', 'CARTAO_DEBITO', 'PIX', 'FIADO', 'OUTRO', name='metodopagamento'), nullable=False),
    sa.Column('status_pagamento', sa.Enum('PENDENTE', 'APROVADO', 'REJEITADO', 'CANCELADO', name='statuspagamento'), nullable=False),
    sa.Column('detalhes_transacao', sa.String(), nullable=True),
    sa.Column('observacoes', sa.Text(), nullable=True),
    sa.Column('data_pagamento', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id_cliente'], ['clientes.id'], ),
    sa.ForeignKeyConstraint(['id_comanda'], ['comandas.id'], ),
    sa.ForeignKeyConstraint(['id_pedido'], ['pedidos.id'], ),
    sa.ForeignKeyConstraint(['id_usuario_registrou'], ['users.id'], ),
    sa.ForeignKeyConstraint(['id_venda'], ['vendas.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pagamentos_id'), 'pagamentos', ['id'], unique=False)
    op.create_table('venda_produto',
    sa.Column('id_venda', sa.Integer(), nullable=False),
    sa.Column('id_produto', sa.Integer(), nullable=False),
    sa.Column('quantidade_vendida', sa.Integer(), nullable=False),
    sa.Column('preco_unitario_na_venda', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['id_produto'], ['produtos.id'], ),
    sa.ForeignKeyConstraint(['id_venda'], ['vendas.id'], ),
    sa.PrimaryKeyConstraint('id_venda', 'id_produto')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('venda_produto')
    op.drop_index(op.f('ix_pagamentos_id'), table_name='pagamentos')
    op.drop_table('pagamentos')
    op.drop_index(op.f('ix_itens_pedido_id'), table_name='itens_pedido')
    op.drop_table('itens_pedido')
    op.drop_index(op.f('ix_vendas_id'), table_name='vendas')
    op.drop_table('vendas')
    op.drop_index(op.f('ix_pedidos_id'), table_name='pedidos')
    op.drop_table('pedidos')
    op.drop_index(op.f('ix_fiados_id'), table_name='fiados')
    op.drop_table('fiados')
    op.drop_index(op.f('ix_comandas_qr_code_comanda_hash'), table_name='comandas')
    op.drop_index(op.f('ix_comandas_id'), table_name='comandas')
    op.drop_table('comandas')
    op.drop_index(op.f('ix_refresh_tokens_token'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_id'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_index(op.f('ix_produtos_nome'), table_name='produtos')
    op.drop_index(op.f('ix_produtos_id'), table_name='produtos')
    op.drop_index(op.f('ix_produtos_categoria_id'), table_name='produtos')
    op.drop_table('produtos')
    op.drop_index(op.f('ix_password_reset_tokens_token'), table_name='password_reset_tokens')
    op.drop_index(op.f('ix_password_reset_tokens_id'), table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
    op.drop_index(op.f('ix_mesas_qr_code_hash'), table_name='mesas')
    op.drop_index(op.f('ix_mesas_numero_identificador'), table_name='mesas')
    op.drop_index(op.f('ix_mesas_id'), table_name='mesas')
    op.drop_table('mesas')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_imagem_url'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_clientes_telefone'), table_name='clientes')
    op.drop_index(op.f('ix_clientes_nome'), table_name='clientes')
    op.drop_index(op.f('ix_clientes_imagem_url'), table_name='clientes')
    op.drop_index(op.f('ix_clientes_id'), table_name='clientes')
    op.drop_table('clientes')
    op.drop_index(op.f('ix_categorias_nome'), table_name='categorias')
    op.drop_index(op.f('ix_categorias_id'), table_name='categorias')
    op.drop_table('categorias')
    # ### end Alembic commands ###
