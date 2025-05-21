from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from fastapi import HTTPException, status
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

from sqlalchemy.orm import selectinload

from app.models.pedido import Pedido as PedidoModel, StatusPedido
from app.models.item_pedido import ItemPedido as ItemPedidoModel, StatusPedidoEnum
from app.models.produto import Produto as ProdutoModel
from app.models.comanda import Comanda as ComandaModel, StatusComanda
from app.models.mesa import Mesa as MesaModel

from app.schemas.pedido_schemas import PedidoCreate, Pedido
from app.schemas.item_pedido_schemas import ItemPedido as ItemPedidoSchema
from app.services import comanda_service, produto_service

from app.services.redis_service import redis_service_instance, WebSocketMessage
from app.schemas.websocket_schemas import ComandaStatusUpdatePayload, NotificationPayload

from loguru import logger

from app.services.user_service import user_service, UserService


class PedidoService:
    async def criar_pedido(self, db: AsyncSession, pedido_data: PedidoCreate) -> Dict[str, Any]:
        """
        Cria um novo pedido com seus itens associados.
        Retorna um dicionário com os dados do pedido e seus itens para serialização segura.
        """
        # Verificar se a comanda existe
        comanda = await comanda_service.get_comanda_by_id(db, pedido_data.id_comanda)
        if not comanda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comanda com ID {pedido_data.id_comanda} não encontrada"
            )

        # if comanda.status_comanda != StatusComanda.ABERTA:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=f"A comanda {comanda.id} não permite novos pedidos (Status: {comanda.status_comanda.value})"
        #     )

        # Verificar se o usuário existe
        if pedido_data.id_usuario_registrou:
            usuario = await user_service.get_user_by_id(db, pedido_data.id_usuario_registrou)
            if not usuario:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Usuário com ID {pedido_data.id_usuario_registrou} não encontrado"
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

        # Lista para armazenar os itens criados
        itens_criados = []

        # Criar os itens do pedido
        for item_data in pedido_data.itens:
            # Verificar se o produto existe
            # Corrigido para usar o método correto obter_produto em vez de get_produto_by_id
            produto = await produto_service.obter_produto(db, item_data.id_produto)
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

            # Obter o preço unitário diretamente do produto
            preco_unitario = produto.preco_unitario

            # Calcular o preço total do item usando o preço do produto
            preco_total_item = preco_unitario * item_data.quantidade

            # Criar o item do pedido
            novo_item = ItemPedidoModel(
                id_pedido=novo_pedido.id,
                id_comanda=pedido_data.id_comanda,
                id_produto=item_data.id_produto,
                quantidade=item_data.quantidade,
                preco_unitario=preco_unitario,  # Usando o preço do produto
                preco_total=preco_unitario * item_data.quantidade,  # Calculando o preço total
                observacoes=item_data.observacoes,  # Corrigido para observacoes (plural)
                status=StatusPedidoEnum.RECEBIDO,  # Definindo status inicial
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # Garantir que o preço total seja calculado corretamente
            novo_item.calcular_preco_total()

            db.add(novo_item)

            # Armazenar dados do item para retorno
            itens_criados.append({
                "id": None,  # Será atualizado após o commit
                "id_pedido": novo_pedido.id,
                "id_comanda": pedido_data.id_comanda,  # Adicionado campo id_comanda
                "id_produto": item_data.id_produto,
                "quantidade": item_data.quantidade,
                "preco_unitario": float(preco_unitario),
                "preco_total": float(preco_total_item),
                "observacoes": item_data.observacoes,
                "status": StatusPedidoEnum.RECEBIDO.value,  # Adicionado campo status
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()  # Adicionado campo updated_at
            })

        # Atualizar o status da comanda para PAGA_PARCIALMENTE se estiver ABERTA
        # Corrigido para usar um status válido do enum StatusComanda
        if comanda.status_comanda == StatusComanda.ABERTA:
            comanda.status_comanda = StatusComanda.PAGA_PARCIALMENTE
            comanda.updated_at = datetime.now()

        # Recalcular o valor total da comanda
        await comanda_service.recalculate_comanda_totals(db, comanda.id)

        # Commit das alterações
        await db.commit()

        # Buscar o pedido com seus itens carregados para retorno seguro
        query = (
            select(PedidoModel)
            .options(selectinload(PedidoModel.itens))
            .where(PedidoModel.id == novo_pedido.id)
        )

        result = await db.execute(query)
        pedido_completo = result.scalars().first()

        # Converter para dicionário para evitar acesso lazy fora do contexto assíncrono
        pedido_dict = {
            "id": pedido_completo.id,
            "id_comanda": pedido_completo.id_comanda,
            "id_usuario_registrou": pedido_completo.id_usuario_registrou,
            "mesa_id": pedido_completo.mesa_id,  # Adicionado campo mesa_id
            "tipo_pedido": pedido_completo.tipo_pedido.value,
            "status_geral_pedido": pedido_completo.status_geral_pedido.value,
            "observacoes_pedido": pedido_completo.observacoes_pedido,
            "motivo_cancelamento": pedido_completo.motivo_cancelamento,  # Adicionado campo motivo_cancelamento
            "created_at": pedido_completo.created_at.isoformat() if pedido_completo.created_at else None,
            "updated_at": pedido_completo.updated_at.isoformat() if pedido_completo.updated_at else None,
            "itens": []
        }

        # Adicionar itens ao dicionário
        for item in pedido_completo.itens:
            item_dict = {
                "id": item.id,
                "id_pedido": item.id_pedido,
                "id_comanda": item.id_comanda,  # Adicionado campo id_comanda
                "id_produto": item.id_produto,
                "quantidade": item.quantidade,
                "preco_unitario": float(item.preco_unitario),
                "preco_total": float(item.preco_total),
                "observacoes": item.observacoes,
                "status": item.status.value,  # Adicionado campo status
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None  # Adicionado campo updated_at
            }
            pedido_dict["itens"].append(item_dict)

        # Notificar sobre o novo pedido
        await self._notificar_novo_pedido(pedido_completo)

        return pedido_dict

    async def listar_pedidos(
            self,
            db: AsyncSession,
            status: Optional[str] = None,
            data_inicio: Optional[str] = None,
            data_fim: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista pedidos com filtros opcionais.
        Retorna uma lista de dicionários com os dados dos pedidos para serialização segura.
        """
        query = (
            select(PedidoModel)
            .options(selectinload(PedidoModel.itens))
        )

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
        pedidos = result.scalars().all()

        # Converter para lista de dicionários
        pedidos_list = []
        for pedido in pedidos:
            pedido_dict = {
                "id": pedido.id,
                "id_comanda": pedido.id_comanda,
                "id_usuario_registrou": pedido.id_usuario_registrou,
                "mesa_id": pedido.mesa_id,  # Adicionado campo mesa_id
                "tipo_pedido": pedido.tipo_pedido.value,
                "status_geral_pedido": pedido.status_geral_pedido.value,
                "observacoes_pedido": pedido.observacoes_pedido,
                "motivo_cancelamento": pedido.motivo_cancelamento,  # Adicionado campo motivo_cancelamento
                "created_at": pedido.created_at.isoformat() if pedido.created_at else None,
                "updated_at": pedido.updated_at.isoformat() if pedido.updated_at else None,
                "itens": []
            }

            # Adicionar itens ao dicionário
            for item in pedido.itens:
                item_dict = {
                    "id": item.id,
                    "id_pedido": item.id_pedido,
                    "id_comanda": item.id_comanda,  # Adicionado campo id_comanda
                    "id_produto": item.id_produto,
                    "quantidade": item.quantidade,
                    "preco_unitario": float(item.preco_unitario),
                    "preco_total": float(item.preco_total),
                    "observacoes": item.observacoes,
                    "status": item.status.value,  # Adicionado campo status
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None
                    # Adicionado campo updated_at
                }
                pedido_dict["itens"].append(item_dict)

            pedidos_list.append(pedido_dict)

        return pedidos_list

    async def buscar_pedido(self, db: AsyncSession, pedido_id: int) -> Dict[str, Any]:
        """
        Busca um pedido pelo ID com seus itens carregados.
        Retorna um dicionário com os dados do pedido e seus itens para serialização segura.
        """
        if not pedido_id or pedido_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de pedido inválido"
            )

        query = (
            select(PedidoModel)
            .options(selectinload(PedidoModel.itens))
            .where(PedidoModel.id == pedido_id)
        )

        result = await db.execute(query)
        pedido = result.scalars().first()

        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pedido com ID {pedido_id} não encontrado"
            )

        # Converter para dicionário para evitar acesso lazy fora do contexto assíncrono
        pedido_dict = {
            "id": pedido.id,
            "id_comanda": pedido.id_comanda,
            "id_usuario_registrou": pedido.id_usuario_registrou,
            "mesa_id": pedido.mesa_id,  # Adicionado campo mesa_id
            "tipo_pedido": pedido.tipo_pedido.value,
            "status_geral_pedido": pedido.status_geral_pedido.value,
            "observacoes_pedido": pedido.observacoes_pedido,
            "motivo_cancelamento": pedido.motivo_cancelamento,  # Adicionado campo motivo_cancelamento
            "created_at": pedido.created_at.isoformat() if pedido.created_at else None,
            "updated_at": pedido.updated_at.isoformat() if pedido.updated_at else None,
            "itens": []
        }

        # Adicionar itens ao dicionário
        for item in pedido.itens:
            item_dict = {
                "id": item.id,
                "id_pedido": item.id_pedido,
                "id_comanda": item.id_comanda,  # Adicionado campo id_comanda
                "id_produto": item.id_produto,
                "quantidade": item.quantidade,
                "preco_unitario": float(item.preco_unitario),
                "preco_total": float(item.preco_total),
                "observacoes": item.observacoes,
                "status": item.status.value,  # Adicionado campo status
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None  # Adicionado campo updated_at
            }
            pedido_dict["itens"].append(item_dict)

        return pedido_dict

    async def atualizar_status_pedido(
            self,
            db: AsyncSession,
            pedido_id: int,
            novo_status: StatusPedido
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Atualiza o status de um pedido.
        Retorna o pedido atualizado como dicionário e uma mensagem de sucesso ou erro.
        """
        # Validar ID
        if not pedido_id or pedido_id <= 0:
            return None, "ID de pedido inválido"

        # Buscar o pedido
        query = (
            select(PedidoModel)
            .options(selectinload(PedidoModel.itens))
            .where(PedidoModel.id == pedido_id)
        )

        result = await db.execute(query)
        pedido = result.scalars().first()

        if not pedido:
            return None, f"Pedido com ID {pedido_id} não encontrado"

        # Verificar se a transição de status é válida
        if not self._validar_transicao_status(pedido.status_geral_pedido, novo_status):
            return None, f"Transição de status inválida: {pedido.status_geral_pedido.value} -> {novo_status.value}"

        # Atualizar o status
        pedido.status_geral_pedido = novo_status
        pedido.updated_at = datetime.now()

        # Se o pedido for cancelado, cancelar todos os itens
        if novo_status == StatusPedido.CANCELADO:
            for item in pedido.itens:
                item.status = StatusPedidoEnum.CANCELADO
                item.updated_at = datetime.now()

        # Commit das alterações
        await db.commit()
        await db.refresh(pedido)

        # Notificar sobre a atualização de status
        await self._notificar_atualizacao_status_pedido(pedido)

        # Converter para dicionário para evitar acesso lazy fora do contexto assíncrono
        pedido_dict = {
            "id": pedido.id,
            "id_comanda": pedido.id_comanda,
            "id_usuario_registrou": pedido.id_usuario_registrou,
            "mesa_id": pedido.mesa_id,  # Adicionado campo mesa_id
            "tipo_pedido": pedido.tipo_pedido.value,
            "status_geral_pedido": pedido.status_geral_pedido.value,
            "observacoes_pedido": pedido.observacoes_pedido,
            "motivo_cancelamento": pedido.motivo_cancelamento,  # Adicionado campo motivo_cancelamento
            "created_at": pedido.created_at.isoformat() if pedido.created_at else None,
            "updated_at": pedido.updated_at.isoformat() if pedido.updated_at else None,
            "itens": []
        }

        # Adicionar itens ao dicionário
        for item in pedido.itens:
            item_dict = {
                "id": item.id,
                "id_pedido": item.id_pedido,
                "id_comanda": item.id_comanda,  # Adicionado campo id_comanda
                "id_produto": item.id_produto,
                "quantidade": item.quantidade,
                "preco_unitario": float(item.preco_unitario),
                "preco_total": float(item.preco_total),
                "observacoes": item.observacoes,
                "status": item.status.value,  # Adicionado campo status
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None  # Adicionado campo updated_at
            }
            pedido_dict["itens"].append(item_dict)

        return pedido_dict, f"Status do pedido atualizado para {novo_status.value}"

    async def cancelar_pedido(self, db: AsyncSession, pedido_id: int) -> Optional[Dict[str, Any]]:
        """
        Cancela um pedido e todos os seus itens.
        Retorna o pedido cancelado como dicionário.
        """
        # Validar ID
        if not pedido_id or pedido_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de pedido inválido"
            )

        pedido_dict, mensagem = await self.atualizar_status_pedido(
            db, pedido_id, StatusPedido.CANCELADO
        )

        if not pedido_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=mensagem
            )

        return pedido_dict

    async def listar_pedidos_por_usuario(
            self,
            db: AsyncSession,
            usuario_id: int
    ) -> List[Dict[str, Any]]:
        """
        Lista pedidos registrados por um usuário específico.
        Retorna uma lista de dicionários com os dados dos pedidos para serialização segura.
        """
        # Validar ID
        if not usuario_id or usuario_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de usuário inválido"
            )

        query = (
            select(PedidoModel)
            .options(selectinload(PedidoModel.itens))
            .where(PedidoModel.id_usuario_registrou == usuario_id)
            .order_by(PedidoModel.created_at.desc())
        )

        result = await db.execute(query)
        pedidos = result.scalars().all()

        # Converter para lista de dicionários
        pedidos_list = []
        for pedido in pedidos:
            pedido_dict = {
                "id": pedido.id,
                "id_comanda": pedido.id_comanda,
                "id_usuario_registrou": pedido.id_usuario_registrou,
                "mesa_id": pedido.mesa_id,  # Adicionado campo mesa_id
                "tipo_pedido": pedido.tipo_pedido.value,
                "status_geral_pedido": pedido.status_geral_pedido.value,
                "observacoes_pedido": pedido.observacoes_pedido,
                "motivo_cancelamento": pedido.motivo_cancelamento,  # Adicionado campo motivo_cancelamento
                "created_at": pedido.created_at.isoformat() if pedido.created_at else None,
                "updated_at": pedido.updated_at.isoformat() if pedido.updated_at else None,
                "itens": []
            }

            # Adicionar itens ao dicionário
            for item in pedido.itens:
                item_dict = {
                    "id": item.id,
                    "id_pedido": item.id_pedido,
                    "id_comanda": item.id_comanda,  # Adicionado campo id_comanda
                    "id_produto": item.id_produto,
                    "quantidade": item.quantidade,
                    "preco_unitario": float(item.preco_unitario),
                    "preco_total": float(item.preco_total),
                    "observacoes": item.observacoes,
                    "status": item.status.value,  # Adicionado campo status
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None
                    # Adicionado campo updated_at
                }
                pedido_dict["itens"].append(item_dict)

            pedidos_list.append(pedido_dict)

        return pedidos_list

    def _validar_transicao_status(
            self,
            status_atual: StatusPedido,
            novo_status: StatusPedido
    ) -> bool:
        """
        Valida se a transição de status é permitida.
        """
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

        return novo_status in transicoes_validas.get(status_atual, [])

    async def _notificar_novo_pedido(self, pedido: PedidoModel) -> None:
        """
        Notifica sobre um novo pedido.
        """
        try:
            # Definir mesa_numero sem necessidade de consulta ao banco
            mesa_numero = "N/A"

            # Preparar payload da notificação
            payload = NotificationPayload(
                title="Novo Pedido Registrado",
                message=f"Mesa {mesa_numero}: Novo pedido com {len(pedido.itens)} item(ns)",
                details={
                    "pedido_id": str(pedido.id),
                    "comanda_id": str(pedido.id_comanda),
                    "mesa_id": str(pedido.mesa_id) if pedido.mesa_id else "N/A",
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
            # Definir mesa_numero sem necessidade de consulta ao banco
            mesa_numero = "N/A"

            # Preparar payload da notificação
            payload = NotificationPayload(
                title="Status de Pedido Atualizado",
                message=f"Mesa {mesa_numero}: Pedido {pedido.id} atualizado para {pedido.status_geral_pedido.value}",
                details={
                    "pedido_id": str(pedido.id),
                    "comanda_id": str(pedido.id_comanda),
                    "mesa_id": str(pedido.mesa_id) if pedido.mesa_id else "N/A",
                    "mesa_numero": mesa_numero,
                    "tipo_pedido": pedido.tipo_pedido.value,
                    "status": pedido.status_geral_pedido.value
                }
            )

            # Publicar mensagem
            await redis_service_instance.publish_message(
                channel="staff_notifications",
                message=WebSocketMessage(type="status_pedido_atualizado", payload=payload.model_dump())
            )
        except Exception as e:
            logger.error(f"Erro ao notificar atualização de status de pedido: {str(e)}")


# Instância do serviço para uso nas rotas
pedido_service = PedidoService()
