from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from fastapi import HTTPException, status
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
import uuid
from datetime import datetime

from app.models.pedido import Pedido as PedidoModel, StatusPedido, TipoPedido
from app.models.item_pedido import ItemPedido as ItemPedidoModel
from app.models.produto import Produto as ProdutoModel
from app.models.comanda import Comanda as ComandaModel, StatusComanda
from app.models.mesa import Mesa as MesaModel
from app.schemas.comanda_schemas import ComandaCreate

from app.schemas.pedido_schemas import (
    PedidoCreate, Pedido, ItemPedidoCreate, ItemPedido, StatusPedido as SchemaStatusPedido
)
from app.schemas.public_pedido_schemas import (
    PedidoPublicCreateSchema, ItemPedidoPublicCreateSchema,
    PedidoPublicResponseSchema, ItemPedidoPublicResponseSchema
)

from app.services import comanda_service, produto_service
from app.services.redis_service import redis_service_instance, WebSocketMessage
from app.schemas.websocket_schemas import ComandaStatusUpdatePayload, NotificationPayload

from loguru import logger


class PedidoService:
    async def criar_pedido(self, db: AsyncSession, pedido_data: PedidoCreate) -> PedidoModel:
        """
        Cria um novo pedido com seus itens associados.
        """
        # Verificar se a comanda existe
        comanda = await comanda_service.get_comanda_by_id(db, pedido_data.id_comanda)
        if not comanda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comanda com ID {pedido_data.id_comanda} não encontrada"
            )

        # Verificar se a comanda está em um estado que permite novos pedidos
        if comanda.status_comanda not in [StatusComanda.ABERTA, StatusComanda.EM_ATENDIMENTO]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A comanda {comanda.id} não permite novos pedidos (Status: {comanda.status_comanda.value})"
            )

        # Criar o pedido
        novo_pedido = PedidoModel(
            id_comanda=pedido_data.id_comanda,
            id_usuario_registrou=pedido_data.id_usuario_registrou,
            mesa_id=comanda.id_mesa,  # Associar à mesa da comanda
            tipo_pedido=pedido_data.tipo_pedido,
            status_geral_pedido=pedido_data.status_geral_pedido,
            observacoes_pedido=pedido_data.observacoes_pedido,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.add(novo_pedido)
        await db.flush()  # Para obter o ID do pedido

        # Criar os itens do pedido
        for item_data in pedido_data.itens:
            # Verificar se o produto existe
            produto = await produto_service.get_produto_by_id(db, item_data.id_produto)
            if not produto:
                # Rollback e lançar exceção
                await db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Produto com ID {item_data.id_produto} não encontrado"
                )

            if not produto.disponivel:
                await db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"O produto '{produto.nome}' não está disponível no momento"
                )

            # Calcular o preço total do item
            preco_total_item = item_data.preco_unitario * item_data.quantidade

            # Criar o item do pedido
            novo_item = ItemPedidoModel(
                id_pedido=novo_pedido.id,
                id_produto=item_data.id_produto,
                quantidade=item_data.quantidade,
                preco_unitario=item_data.preco_unitario,
                preco_total_item=preco_total_item,
                observacao=item_data.observacao,
                status_item_pedido=item_data.status_item_pedido,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            db.add(novo_item)

        # Atualizar o status da comanda para EM_ATENDIMENTO se estiver ABERTA
        if comanda.status_comanda == StatusComanda.ABERTA:
            comanda.status_comanda = StatusComanda.EM_ATENDIMENTO
            comanda.updated_at = datetime.now()

        # Recalcular o valor total da comanda
        await comanda_service.recalculate_comanda_totals(db, comanda.id)

        # Commit das alterações
        await db.commit()
        await db.refresh(novo_pedido)

        # Notificar sobre o novo pedido
        await self._notificar_novo_pedido(novo_pedido)

        return novo_pedido

    async def listar_pedidos(
            self,
            db: AsyncSession,
            status: Optional[str] = None,
            data_inicio: Optional[str] = None,
            data_fim: Optional[str] = None
    ) -> List[PedidoModel]:
        """
        Lista pedidos com filtros opcionais.
        """
        query = select(PedidoModel)

        # Aplicar filtros
        if status:
            try:
                status_enum = StatusPedido(status)
                query = query.where(PedidoModel.status_geral_pedido == status_enum)
            except ValueError:
                # Status inválido, ignorar filtro
                pass

        if data_inicio:
            try:
                data_inicio_dt = datetime.fromisoformat(data_inicio)
                query = query.where(PedidoModel.created_at >= data_inicio_dt)
            except ValueError:
                # Data inválida, ignorar filtro
                pass

        if data_fim:
            try:
                data_fim_dt = datetime.fromisoformat(data_fim)
                query = query.where(PedidoModel.created_at <= data_fim_dt)
            except ValueError:
                # Data inválida, ignorar filtro
                pass

        # Ordenar por data de criação (mais recentes primeiro)
        query = query.order_by(PedidoModel.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    async def buscar_pedido(self, db: AsyncSession, pedido_id: int) -> Optional[PedidoModel]:
        """
        Busca um pedido pelo ID.
        """
        query = select(PedidoModel).where(PedidoModel.id == pedido_id)
        result = await db.execute(query)
        return result.scalars().first()

    async def atualizar_status_pedido(
            self,
            db: AsyncSession,
            pedido_id: int,
            novo_status: SchemaStatusPedido
    ) -> Tuple[Optional[PedidoModel], str]:
        """
        Atualiza o status de um pedido.
        Retorna o pedido atualizado e uma mensagem de sucesso ou erro.
        """
        # Buscar o pedido
        pedido = await self.buscar_pedido(db, pedido_id)
        if not pedido:
            return None, f"Pedido com ID {pedido_id} não encontrado"

        # Verificar se a transição de status é válida
        if not self._validar_transicao_status(pedido.status_geral_pedido, novo_status):
            return None, f"Transição de status inválida: {pedido.status_geral_pedido.value} -> {novo_status.value}"

        # Atualizar o status
        pedido.status_geral_pedido = novo_status
        pedido.updated_at = datetime.now()

        # Se o pedido for cancelado, cancelar todos os itens
        if novo_status == SchemaStatusPedido.CANCELADO:
            for item in pedido.itens:
                item.status_item_pedido = SchemaStatusPedido.CANCELADO
                item.updated_at = datetime.now()

        # Commit das alterações
        await db.commit()
        await db.refresh(pedido)

        # Notificar sobre a atualização de status
        await self._notificar_atualizacao_status_pedido(pedido)

        return pedido, f"Status do pedido atualizado para {novo_status.value}"

    async def adicionar_item(
            self,
            db: AsyncSession,
            pedido_id: int,
            item_data: ItemPedidoCreate
    ) -> Optional[ItemPedidoModel]:
        """
        Adiciona um item a um pedido existente.
        """
        # Buscar o pedido
        pedido = await self.buscar_pedido(db, pedido_id)
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

        # Calcular o preço total do item
        preco_total_item = item_data.preco_unitario * item_data.quantidade

        # Criar o item do pedido
        novo_item = ItemPedidoModel(
            id_pedido=pedido_id,
            id_produto=item_data.id_produto,
            quantidade=item_data.quantidade,
            preco_unitario=item_data.preco_unitario,
            preco_total_item=preco_total_item,
            observacao=item_data.observacao,
            status_item_pedido=item_data.status_item_pedido,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.add(novo_item)

        # Recalcular o valor total da comanda
        await comanda_service.recalculate_comanda_totals(db, pedido.id_comanda)

        # Commit das alterações
        await db.commit()
        await db.refresh(novo_item)

        # Notificar sobre o novo item
        await self._notificar_novo_item_pedido(pedido, novo_item)

        return novo_item

    async def remover_item(self, db: AsyncSession, pedido_id: int, item_id: int) -> bool:
        """
        Remove um item de um pedido.
        """
        # Buscar o pedido
        pedido = await self.buscar_pedido(db, pedido_id)
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

        # Notificar sobre a remoção do item
        await self._notificar_remocao_item_pedido(pedido, item)

        return True

    async def cancelar_pedido(self, db: AsyncSession, pedido_id: int) -> Optional[PedidoModel]:
        """
        Cancela um pedido e todos os seus itens.
        """
        pedido, mensagem = await self.atualizar_status_pedido(
            db, pedido_id, SchemaStatusPedido.CANCELADO
        )
        return pedido

    async def listar_pedidos_por_usuario(
            self,
            db: AsyncSession,
            usuario_id: int
    ) -> List[PedidoModel]:
        """
        Lista pedidos registrados por um usuário específico.
        """
        query = select(PedidoModel).where(PedidoModel.id_usuario_registrou == usuario_id)
        query = query.order_by(PedidoModel.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    def _validar_transicao_status(
            self,
            status_atual: StatusPedido,
            novo_status: SchemaStatusPedido
    ) -> bool:
        """
        Valida se a transição de status é permitida.
        """
        # Converter o SchemaStatusPedido para StatusPedido do modelo
        try:
            novo_status_model = StatusPedido(novo_status.value)
        except ValueError:
            return False

        # Definir transições válidas
        transicoes_validas = {
            StatusPedido.RECEBIDO: [
                StatusPedido.EM_PREPARO,
                StatusPedido.CANCELADO
            ],
            StatusPedido.EM_PREPARO: [
                StatusPedido.PRONTO_PARA_ENTREGA,
                StatusPedido.CANCELADO
            ],
            StatusPedido.PRONTO_PARA_ENTREGA: [
                StatusPedido.ENTREGUE_NA_MESA,
                StatusPedido.SAIU_PARA_ENTREGA_EXTERNA,
                StatusPedido.CANCELADO
            ],
            StatusPedido.ENTREGUE_NA_MESA: [
                StatusPedido.CANCELADO
            ],
            StatusPedido.SAIU_PARA_ENTREGA_EXTERNA: [
                StatusPedido.ENTREGUE_CLIENTE_EXTERNO,
                StatusPedido.CANCELADO
            ],
            StatusPedido.ENTREGUE_CLIENTE_EXTERNO: [
                StatusPedido.CANCELADO
            ],
            StatusPedido.CANCELADO: []  # Não permite transição a partir de CANCELADO
        }

        return novo_status_model in transicoes_validas.get(status_atual, [])

    async def _notificar_novo_pedido(self, pedido: PedidoModel) -> None:
        """
        Notifica sobre um novo pedido.
        """
        try:
            # Obter informações da mesa
            mesa = await self._get_mesa_info(pedido.mesa_id)
            mesa_numero = mesa.numero if mesa else str(pedido.mesa_id)

            # Preparar payload da notificação
            payload = NotificationPayload(
                title="Novo Pedido Registrado",
                message=f"Mesa {mesa_numero}: Novo pedido com {len(pedido.itens)} item(ns)",
                details={
                    "pedido_id": str(pedido.id),
                    "comanda_id": str(pedido.id_comanda),
                    "mesa_id": str(pedido.mesa_id),
                    "mesa_numero": mesa_numero,
                    "tipo_pedido": pedido.tipo_pedido.value,
                    "status": pedido.status_geral_pedido.value
                }
            )

            # Publicar mensagem
            await redis_service_instance.publish_message(
                channel="staff_notifications",
                message=WebSocketMessage(type="novo_pedido", payload=payload.model_dump())
            )
        except Exception as e:
            logger.error(f"Erro ao notificar novo pedido: {str(e)}")

    async def _notificar_atualizacao_status_pedido(self, pedido: PedidoModel) -> None:
        """
        Notifica sobre atualização de status de um pedido.
        """
        try:
            # Obter informações da mesa
            mesa = await self._get_mesa_info(pedido.mesa_id)
            mesa_numero = mesa.numero if mesa else str(pedido.mesa_id)

            # Preparar payload da notificação
            payload = NotificationPayload(
                title="Status de Pedido Atualizado",
                message=f"Mesa {mesa_numero}: Pedido {pedido.id} atualizado para {pedido.status_geral_pedido.value}",
                details={
                    "pedido_id": str(pedido.id),
                    "comanda_id": str(pedido.id_comanda),
                    "mesa_id": str(pedido.mesa_id),
                    "mesa_numero": mesa_numero,
                    "tipo_pedido": pedido.tipo_pedido.value,
                    "status": pedido.status_geral_pedido.value
                }
            )

            # Publicar mensagem
            await redis_service_instance.publish_message(
                channel="staff_notifications",
                message=WebSocketMessage(type="atualizacao_status_pedido", payload=payload.model_dump())
            )

            # Notificar também o canal específico da comanda
            payload_comanda = ComandaStatusUpdatePayload(
                comanda_id=str(pedido.id_comanda),
                status_comanda="EM_ATENDIMENTO",  # A comanda continua em atendimento
                message=f"Status do pedido atualizado para {pedido.status_geral_pedido.value}"
            )

            await redis_service_instance.publish_message(
                channel=f"comanda_status:{pedido.id_comanda}",
                message=WebSocketMessage(type="status_update", payload=payload_comanda.model_dump())
            )
        except Exception as e:
            logger.error(f"Erro ao notificar atualização de status do pedido: {str(e)}")

    async def _notificar_novo_item_pedido(self, pedido: PedidoModel, item: ItemPedidoModel) -> None:
        """
        Notifica sobre um novo item adicionado a um pedido.
        """
        try:
            # Obter informações do produto
            produto = await produto_service.get_produto_by_id(None, item.id_produto)
            produto_nome = produto.nome if produto else f"Produto {item.id_produto}"

            # Obter informações da mesa
            mesa = await self._get_mesa_info(pedido.mesa_id)
            mesa_numero = mesa.numero if mesa else str(pedido.mesa_id)

            # Preparar payload da notificação
            payload = NotificationPayload(
                title="Novo Item Adicionado ao Pedido",
                message=f"Mesa {mesa_numero}: {item.quantidade}x {produto_nome} adicionado ao pedido {pedido.id}",
                details={
                    "pedido_id": str(pedido.id),
                    "comanda_id": str(pedido.id_comanda),
                    "mesa_id": str(pedido.mesa_id),
                    "mesa_numero": mesa_numero,
                    "item_id": str(item.id),
                    "produto_id": str(item.id_produto),
                    "produto_nome": produto_nome,
                    "quantidade": item.quantidade,
                    "status_item": item.status_item_pedido.value
                }
            )

            # Publicar mensagem
            await redis_service_instance.publish_message(
                channel="staff_notifications",
                message=WebSocketMessage(type="novo_item_pedido", payload=payload.model_dump())
            )
        except Exception as e:
            logger.error(f"Erro ao notificar novo item de pedido: {str(e)}")

    async def _notificar_remocao_item_pedido(self, pedido: PedidoModel, item: ItemPedidoModel) -> None:
        """
        Notifica sobre a remoção de um item de um pedido.
        """
        try:
            # Obter informações do produto
            produto = await produto_service.get_produto_by_id(None, item.id_produto)
            produto_nome = produto.nome if produto else f"Produto {item.id_produto}"

            # Obter informações da mesa
            mesa = await self._get_mesa_info(pedido.mesa_id)
            mesa_numero = mesa.numero if mesa else str(pedido.mesa_id)

            # Preparar payload da notificação
            payload = NotificationPayload(
                title="Item Removido do Pedido",
                message=f"Mesa {mesa_numero}: {item.quantidade}x {produto_nome} removido do pedido {pedido.id}",
                details={
                    "pedido_id": str(pedido.id),
                    "comanda_id": str(pedido.id_comanda),
                    "mesa_id": str(pedido.mesa_id),
                    "mesa_numero": mesa_numero,
                    "item_id": str(item.id),
                    "produto_id": str(item.id_produto),
                    "produto_nome": produto_nome,
                    "quantidade": item.quantidade
                }
            )

            # Publicar mensagem
            await redis_service_instance.publish_message(
                channel="staff_notifications",
                message=WebSocketMessage(type="remocao_item_pedido", payload=payload.model_dump())
            )
        except Exception as e:
            logger.error(f"Erro ao notificar remoção de item de pedido: {str(e)}")

    async def _get_mesa_info(self, mesa_id: int) -> Optional[MesaModel]:
        """
        Obtém informações da mesa.
        """
        # Esta função deveria buscar a mesa no banco de dados
        # Como é um placeholder, retornamos None
        return None


# Função para processar pedidos públicos (via QRCode)
async def processar_pedido_publico(
        db: AsyncSession,
        mesa_id: int,
        pedido_public_data: PedidoPublicCreateSchema,
        mesa_numero: Optional[str] = None
, item_pedido_service=ItemPedido) -> PedidoPublicResponseSchema:
    """
    Processa um pedido feito por um cliente através da interface pública (QRCode da mesa).
    1. Encontra ou cria uma comanda ativa para a mesa.
    2. Valida os produtos solicitados.
    3. Adiciona os itens à comanda.
    4. Recalcula o total da comanda.
    5. Notifica a equipe sobre o novo pedido/itens.
    6. Retorna uma confirmação para o cliente.
    """

    # 1. Encontrar ou criar uma comanda ativa para a mesa
    comanda_ativa = await comanda_service.get_active_comanda_by_mesa_id(db, mesa_id)

    if not comanda_ativa:
        # Se não houver comanda ativa, criar uma nova
        nova_comanda_data = ComandaCreate(
            id_mesa=mesa_id,
            id_cliente=None,
            id_usuario_abriu=None,
            status_comanda=StatusComanda.ABERTA,
            observacoes="Comanda aberta via QRCode pelo cliente."
        )
        comanda_ativa = await comanda_service.create_comanda(db, comanda_data=nova_comanda_data)
        if not comanda_ativa:
            logger.error(f"Falha ao criar nova comanda para mesa_id: {mesa_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Não foi possível iniciar uma nova comanda para sua mesa."
            )
        logger.info(f"Nova comanda {comanda_ativa.id} criada para mesa {mesa_id} via QRCode.")
    elif comanda_ativa.status_comanda not in [StatusComanda.ABERTA, StatusComanda.EM_ATENDIMENTO]:
        logger.warning(
            f"Tentativa de adicionar itens à comanda {comanda_ativa.id} (mesa {mesa_id}) com status {comanda_ativa.status_comanda}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A comanda atual da mesa não permite novos itens (Status: {comanda_ativa.status_comanda.value}). Chame um garçom."
        )

    itens_confirmados_response: List[ItemPedidoPublicResponseSchema] = []
    valor_total_novos_itens = Decimal(0)

    # 2. Validar produtos e 3. Adicionar itens à comanda
    if not pedido_public_data.itens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum item fornecido no pedido."
        )

    for item_data in pedido_public_data.itens:
        produto = await produto_service.get_produto_by_id(db, item_data.produto_id)
        if not produto:
            logger.warning(
                f"Produto com ID {item_data.produto_id} não encontrado ao processar pedido para comanda {comanda_ativa.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produto com ID {item_data.produto_id} não encontrado no cardápio."
            )

        if not produto.disponivel:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"O produto '{produto.nome}' não está disponível no momento."
            )

        preco_unitario_item = produto.preco_venda
        preco_total_item_calculado = preco_unitario_item * item_data.quantidade

        novo_item_pedido_data = ItemPedidoCreate(
            id_comanda=comanda_ativa.id,
            id_produto=item_data.produto_id,
            quantidade=item_data.quantidade,
            preco_unitario=preco_unitario_item,
            observacao=item_data.observacao,
            status_item_pedido=StatusPedido.RECEBIDO
        )

        item_criado = await item_pedido_service.create_item_pedido(db, item_pedido_data=novo_item_pedido_data)
        if not item_criado:
            logger.error(
                f"Falha ao criar item_pedido para produto {item_data.produto_id} na comanda {comanda_ativa.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao adicionar o produto '{produto.nome}' ao seu pedido."
            )

        valor_total_novos_itens += preco_total_item_calculado
        itens_confirmados_response.append(
            ItemPedidoPublicResponseSchema(
                produto_nome=produto.nome,
                quantidade=item_data.quantidade,
                preco_unitario=preco_unitario_item,
                preco_total_item=preco_total_item_calculado,
                observacao=item_data.observacao
            )
        )

    # 4. Recalcular o valor total da comanda e atualizar status
    comanda_atualizada = await comanda_service.recalculate_comanda_totals_and_update_status(
        db, comanda_id=comanda_ativa.id
    )
    if not comanda_atualizada:
        logger.error(f"Falha ao recalcular totais para comanda {comanda_ativa.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao finalizar o processamento do seu pedido."
        )

    # 5. Notificar a equipe sobre o novo pedido/itens
    mensagem_notificacao_staff = NotificationPayload(
        title="Novo Pedido/Itens Adicionados via QRCode",
        message=f"Mesa {mesa_numero if mesa_numero else mesa_id} adicionou {len(pedido_public_data.itens)} tipo(s) de item(ns) à comanda {comanda_atualizada.id}. Total de novos itens: R$ {valor_total_novos_itens:.2f}.",
        details={
            "comanda_id": comanda_atualizada.id,
            "mesa_id": mesa_id,
            "mesa_numero": mesa_numero,
            "numero_de_itens_adicionados": len(pedido_public_data.itens)
        }
    )
    await redis_service_instance.publish_message(
        channel="staff_notifications",
        message=WebSocketMessage(type="notification", payload=mensagem_notificacao_staff.model_dump())
    )

    # Notificar também o canal específico da comanda
    payload_atualizacao_comanda = ComandaStatusUpdatePayload(
        comanda_id=str(comanda_atualizada.id),
        status_comanda=comanda_atualizada.status_comanda.value,
        message=f"{len(pedido_public_data.itens)} item(ns) adicionado(s) à sua comanda."
    )
    await redis_service_instance.publish_message(
        channel=f"comanda_status:{comanda_atualizada.id}",
        message=WebSocketMessage(type="status_update", payload=payload_atualizacao_comanda.model_dump())
    )

    logger.info(
        f"Pedido processado com sucesso para comanda {comanda_atualizada.id} (Mesa {mesa_id}). {len(itens_confirmados_response)} itens adicionados.")

    # 6. Retornar uma confirmação para o cliente
    return PedidoPublicResponseSchema(
        id_comanda=str(comanda_atualizada.id),
        status_comanda=comanda_atualizada.status_comanda.value,
        mesa_numero=mesa_numero,
        itens_confirmados=itens_confirmados_response,
        valor_total_comanda_atual=comanda_atualizada.valor_total_calculado,
        mensagem_confirmacao="Seu pedido foi recebido e está sendo processado!",
        qr_code_comanda_hash=comanda_atualizada.qr_code_comanda_hash
    )


# Instanciar o serviço
pedido_service = PedidoService()
