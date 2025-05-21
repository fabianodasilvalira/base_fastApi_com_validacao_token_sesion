from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from fastapi import HTTPException, status
from typing import List, Optional, Dict
from datetime import datetime

from app.models.item_pedido import ItemPedido as ItemPedidoModel
from app.models.pedido import Pedido as PedidoModel, StatusPedido
from app.models.produto import Produto as ProdutoModel
from app.schemas.item_pedido_schemas import ItemPedidoCreate, ItemPedidoUpdate
from app.services import produto_service, comanda_service


class ItemPedidoService:
    async def adicionar_item(
            self,
            db: AsyncSession,
            pedido_id: int,
            item_data: ItemPedidoCreate
    ) -> Optional[ItemPedidoModel]:
        """
        Adiciona um item a um pedido existente.
        """
        # Validar ID do pedido
        if not pedido_id or pedido_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de pedido inválido"
            )

        # Buscar o pedido
        query = select(PedidoModel).where(PedidoModel.id == pedido_id)
        result = await db.execute(query)
        pedido = result.scalars().first()

        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pedido com ID {pedido_id} não encontrado"
            )

        # Verificar se o pedido está em um estado que permite adicionar itens
        if pedido.status_geral_pedido not in [StatusPedido.RECEBIDO, StatusPedido.EM_PREPARO]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"O pedido está em status {pedido.status_geral_pedido.value} e não permite adicionar novos itens"
            )

        # Validar quantidade
        if item_data.quantidade <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A quantidade deve ser maior que zero"
            )

        # Verificar se o produto existe
        produto = await produto_service.get_produto_by_id(db, item_data.id_produto)
        if not produto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produto com ID {item_data.id_produto} não encontrado"
            )

        if not produto.disponivel:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"O produto '{produto.nome}' não está disponível no momento"
            )

        # Usar o preço do produto
        preco_unitario = produto.preco_unitario

        # Criar o item do pedido
        novo_item = ItemPedidoModel(
            id_pedido=pedido_id,
            id_comanda=pedido.id_comanda,
            id_produto=item_data.id_produto,
            quantidade=item_data.quantidade,
            preco_unitario=preco_unitario,
            preco_total=preco_unitario * item_data.quantidade,  # Calculando o preço total
            observacoes=item_data.observacoes,
            created_at=datetime.now()
            # Removida a referência a updated_at que não existe no banco
        )

        # Garantir que o preço total seja calculado corretamente
        novo_item.calcular_preco_total()

        db.add(novo_item)

        # Recalcular o valor total da comanda
        await comanda_service.recalculate_comanda_totals(db, pedido.id_comanda)

        # Commit das alterações
        await db.commit()
        await db.refresh(novo_item)

        return novo_item

    async def atualizar_item(
            self,
            db: AsyncSession,
            pedido_id: int,
            item_id: int,
            item_update: ItemPedidoUpdate
    ) -> Optional[ItemPedidoModel]:
        """
        Atualiza um item de um pedido.
        """
        # Validar IDs
        if not pedido_id or pedido_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de pedido inválido"
            )

        if not item_id or item_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de item inválido"
            )

        # Buscar o item
        query = select(ItemPedidoModel).where(
            (ItemPedidoModel.id == item_id) &
            (ItemPedidoModel.id_pedido == pedido_id)
        )
        result = await db.execute(query)
        item = result.scalars().first()

        if not item:
            return None

        # Buscar o pedido para verificar status
        query_pedido = select(PedidoModel).where(PedidoModel.id == pedido_id)
        result_pedido = await db.execute(query_pedido)
        pedido = result_pedido.scalars().first()

        if not pedido:
            return None

        # Verificar se o pedido está em um estado que permite atualizar itens
        if pedido.status_geral_pedido not in [StatusPedido.RECEBIDO, StatusPedido.EM_PREPARO]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"O pedido está em status {pedido.status_geral_pedido.value} e não permite atualizar itens"
            )

        # Validar quantidade se fornecida
        if item_update.quantidade is not None:
            if item_update.quantidade <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A quantidade deve ser maior que zero"
                )
            item.quantidade = item_update.quantidade

        if item_update.observacoes is not None:
            item.observacoes = item_update.observacoes

        # Removida a atualização de updated_at que não existe no banco

        # Recalcular o valor total da comanda
        await comanda_service.recalculate_comanda_totals(db, pedido.id_comanda)

        # Commit das alterações
        await db.commit()
        await db.refresh(item)

        return item

    async def remover_item(
            self,
            db: AsyncSession,
            pedido_id: int,
            item_id: int
    ) -> bool:
        """
        Remove um item de um pedido.
        """
        # Validar IDs
        if not pedido_id or pedido_id <= 0:
            return False

        if not item_id or item_id <= 0:
            return False

        # Buscar o pedido
        query_pedido = select(PedidoModel).where(PedidoModel.id == pedido_id)
        result_pedido = await db.execute(query_pedido)
        pedido = result_pedido.scalars().first()

        if not pedido:
            return False

        # Verificar se o pedido está em um estado que permite remover itens
        if pedido.status_geral_pedido not in [StatusPedido.RECEBIDO, StatusPedido.EM_PREPARO]:
            return False

        # Buscar o item
        query = select(ItemPedidoModel).where(
            (ItemPedidoModel.id == item_id) &
            (ItemPedidoModel.id_pedido == pedido_id)
        )
        result = await db.execute(query)
        item = result.scalars().first()

        if not item:
            return False

        # Remover o item
        await db.execute(
            delete(ItemPedidoModel).where(
                (ItemPedidoModel.id == item_id) &
                (ItemPedidoModel.id_pedido == pedido_id)
            )
        )

        # Recalcular o valor total da comanda
        await comanda_service.recalculate_comanda_totals(db, pedido.id_comanda)

        # Commit das alterações
        await db.commit()

        return True

    async def listar_itens_por_pedido(
            self,
            db: AsyncSession,
            pedido_id: int
    ) -> List[ItemPedidoModel]:
        """
        Lista todos os itens de um pedido específico.
        """
        # Validar ID
        if not pedido_id or pedido_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de pedido inválido"
            )

        # Verificar se o pedido existe
        query_pedido = select(PedidoModel).where(PedidoModel.id == pedido_id)
        result_pedido = await db.execute(query_pedido)
        pedido = result_pedido.scalars().first()

        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pedido com ID {pedido_id} não encontrado"
            )

        # Buscar itens do pedido
        query = select(ItemPedidoModel).where(ItemPedidoModel.id_pedido == pedido_id)
        result = await db.execute(query)
        return result.scalars().all()

    async def obter_item(
            self,
            db: AsyncSession,
            pedido_id: int,
            item_id: int
    ) -> Optional[ItemPedidoModel]:
        """
        Obtém detalhes de um item específico de um pedido.
        """
        # Validar IDs
        if not pedido_id or pedido_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de pedido inválido"
            )

        if not item_id or item_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de item inválido"
            )

        # Buscar o item
        query = select(ItemPedidoModel).where(
            (ItemPedidoModel.id == item_id) &
            (ItemPedidoModel.id_pedido == pedido_id)
        )
        result = await db.execute(query)
        return result.scalars().first()


# Instância do serviço para uso nas rotas
item_pedido_service = ItemPedidoService()
