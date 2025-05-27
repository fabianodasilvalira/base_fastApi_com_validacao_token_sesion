import redis
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from fastapi import HTTPException, status
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

from sqlalchemy.orm import selectinload, joinedload

from app.models.pedido import Pedido as PedidoModel, StatusPedido
from app.models.item_pedido import ItemPedido as ItemPedidoModel, StatusPedidoEnum
from app.models.produto import Produto as ProdutoModel
from app.models.comanda import Comanda as ComandaModel, StatusComanda
from app.models.mesa import Mesa as MesaModel

from app.schemas.pedido_schemas import PedidoCreate, Pedido, ComandaEmPedido, UsuarioEmPedido, MesaEmPedido
from app.schemas.item_pedido_schemas import ItemPedido as ItemPedidoSchema
from app.services import comanda_service, produto_service

from app.services.redis_service import redis_service_instance, WebSocketMessage
from app.schemas.websocket_schemas import ComandaStatusUpdatePayload, NotificationPayload

from loguru import logger

from app.services.user_service import user_service, UserService


class PedidoService:

    async def criar_pedido(self, db: AsyncSession, pedido_data: PedidoCreate) -> Dict[str, Any]:
        """
        VERSÃO COMPLETAMENTE REESCRITA - Estratégia de transações separadas para garantir persistência.

        Cria um novo pedido com seus itens associados e atualiza a comanda imediatamente.
        """
        try:
            logger.info(f"🚀 Iniciando criação de pedido para comanda {pedido_data.id_comanda}")

            # 1. VERIFICAÇÕES INICIAIS
            comanda = await comanda_service.get_comanda_by_id(db, pedido_data.id_comanda)
            if not comanda:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Comanda com ID {pedido_data.id_comanda} não encontrada"
                )

            if pedido_data.id_usuario_registrou:
                usuario = await user_service.get_user_by_id(db, pedido_data.id_usuario_registrou)
                if not usuario:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Usuário com ID {pedido_data.id_usuario_registrou} não encontrado"
                    )

            # 2. CRIAR PEDIDO
            novo_pedido = PedidoModel(
                id_comanda=pedido_data.id_comanda,
                id_usuario_registrou=pedido_data.id_usuario_registrou,
                mesa_id=comanda.id_mesa,
                tipo_pedido=pedido_data.tipo_pedido,
                status_geral_pedido=pedido_data.status_geral_pedido,
                observacoes_pedido=pedido_data.observacoes_pedido,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            db.add(novo_pedido)
            await db.flush()  # Para obter o ID
            logger.info(f"📝 Pedido criado com ID {novo_pedido.id}")

            # 3. CRIAR ITENS DO PEDIDO
            for item_data in pedido_data.itens:
                produto = await produto_service.obter_produto(db, item_data.id_produto)
                if not produto:
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

                novo_item = ItemPedidoModel(
                    id_pedido=novo_pedido.id,
                    id_comanda=pedido_data.id_comanda,
                    id_produto=item_data.id_produto,
                    quantidade=item_data.quantidade,
                    preco_unitario=produto.preco_unitario,
                    preco_total=produto.preco_unitario * item_data.quantidade,
                    observacoes=item_data.observacoes,
                    status=StatusPedidoEnum.RECEBIDO,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )

                novo_item.calcular_preco_total()
                db.add(novo_item)

            # 4. COMMIT DO PEDIDO E ITENS - PRIMEIRA TRANSAÇÃO
            await db.commit()
            logger.info(f"✅ Pedido {novo_pedido.id} e itens salvos com sucesso")

            # 5. RECALCULAR COMANDA EM TRANSAÇÃO SEPARADA - GARANTIA DE PERSISTÊNCIA
            try:
                logger.info(f"🔄 Iniciando recálculo da comanda {comanda.id}")

                # Usar a função de força recálculo para garantir persistência
                sucesso_recalculo = await comanda_service.force_recalculate_and_commit(db, comanda.id)

                if sucesso_recalculo:
                    logger.info(f"✅ Comanda {comanda.id} recalculada com sucesso")
                else:
                    logger.error(f"❌ Falha no recálculo da comanda {comanda.id}")
                    # Tentar recálculo alternativo
                    await comanda_service.recalculate_comanda_totals(db, comanda.id, fazer_commit=True)

            except Exception as e:
                logger.error(f"💥 ERRO no recálculo da comanda {comanda.id}: {e}")
                # Não falha o pedido, mas tenta recálculo simples
                try:
                    await comanda_service.recalculate_comanda_totals(db, comanda.id, fazer_commit=True)
                except:
                    logger.error(f"💥 FALHA TOTAL no recálculo da comanda {comanda.id}")

            # 6. BUSCAR PEDIDO COMPLETO PARA RETORNO
            query = (
                select(PedidoModel)
                .options(
                    selectinload(PedidoModel.itens),
                    joinedload(PedidoModel.comanda),
                    joinedload(PedidoModel.usuario_registrou),
                    joinedload(PedidoModel.mesa)
                )
                .where(PedidoModel.id == novo_pedido.id)
            )

            result = await db.execute(query)
            pedido_completo = result.scalars().first()

            # 7. CONVERTER PARA DICIONÁRIO
            pedido_dict = {
                "id": pedido_completo.id,
                "comanda": ComandaEmPedido.model_validate(
                    pedido_completo.comanda).model_dump() if pedido_completo.comanda else None,
                "usuario_registrou": UsuarioEmPedido.model_validate(
                    pedido_completo.usuario_registrou).model_dump() if pedido_completo.usuario_registrou else None,
                "mesa": MesaEmPedido.model_validate(
                    pedido_completo.mesa).model_dump() if pedido_completo.mesa else None,
                "tipo_pedido": pedido_completo.tipo_pedido.value,
                "status_geral_pedido": pedido_completo.status_geral_pedido.value,
                "observacoes_pedido": pedido_completo.observacoes_pedido,
                "motivo_cancelamento": pedido_completo.motivo_cancelamento,
                "created_at": pedido_completo.created_at.isoformat() if pedido_completo.created_at else None,
                "updated_at": pedido_completo.updated_at.isoformat() if pedido_completo.updated_at else None,
                "itens": []
            }

            for item in pedido_completo.itens:
                item_dict = {
                    "id": item.id,
                    "id_pedido": item.id_pedido,
                    "id_comanda": item.id_comanda,
                    "id_produto": item.id_produto,
                    "quantidade": item.quantidade,
                    "preco_unitario": float(item.preco_unitario),
                    "preco_total": float(item.preco_total),
                    "observacoes": item.observacoes,
                    "status": item.status.value,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None
                }
                pedido_dict["itens"].append(item_dict)

            # 8. NOTIFICAÇÃO (NÃO CRÍTICA)
            try:
                await self._notificar_novo_pedido_seguro(pedido_dict)
            except Exception as e:
                logger.warning(f"Erro ao notificar novo pedido (não crítico): {e}")

            logger.info(f"🎉 Pedido {novo_pedido.id} criado com sucesso para comanda {comanda.id}")
            return pedido_dict

        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"💥 Erro inesperado ao criar pedido: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro interno ao criar pedido: {str(e)}"
            )

    # ... resto dos métodos permanecem iguais ...
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
                "mesa_id": pedido.mesa_id,
                "tipo_pedido": pedido.tipo_pedido.value,
                "status_geral_pedido": pedido.status_geral_pedido.value,
                "observacoes_pedido": pedido.observacoes_pedido,
                "motivo_cancelamento": pedido.motivo_cancelamento,
                "created_at": pedido.created_at.isoformat() if pedido.created_at else None,
                "updated_at": pedido.updated_at.isoformat() if pedido.updated_at else None,
                "itens": []
            }

            # Adicionar itens ao dicionário
            for item in pedido.itens:
                item_dict = {
                    "id": item.id,
                    "id_pedido": item.id_pedido,
                    "id_comanda": item.id_comanda,
                    "id_produto": item.id_produto,
                    "quantidade": item.quantidade,
                    "preco_unitario": float(item.preco_unitario),
                    "preco_total": float(item.preco_total),
                    "observacoes": item.observacoes,
                    "status": item.status.value,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None
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
            "mesa_id": pedido.mesa_id,
            "tipo_pedido": pedido.tipo_pedido.value,
            "status_geral_pedido": pedido.status_geral_pedido.value,
            "observacoes_pedido": pedido.observacoes_pedido,
            "motivo_cancelamento": pedido.motivo_cancelamento,
            "created_at": pedido.created_at.isoformat() if pedido.created_at else None,
            "updated_at": pedido.updated_at.isoformat() if pedido.updated_at else None,
            "itens": []
        }

        # Adicionar itens ao dicionário
        for item in pedido.itens:
            item_dict = {
                "id": item.id,
                "id_pedido": item.id_pedido,
                "id_comanda": item.id_comanda,
                "id_produto": item.id_produto,
                "quantidade": item.quantidade,
                "preco_unitario": float(item.preco_unitario),
                "preco_total": float(item.preco_total),
                "observacoes": item.observacoes,
                "status": item.status.value,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None
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
            "mesa_id": pedido.mesa_id,
            "tipo_pedido": pedido.tipo_pedido.value,
            "status_geral_pedido": pedido.status_geral_pedido.value,
            "observacoes_pedido": pedido.observacoes_pedido,
            "motivo_cancelamento": pedido.motivo_cancelamento,
            "created_at": pedido.created_at.isoformat() if pedido.created_at else None,
            "updated_at": pedido.updated_at.isoformat() if pedido.updated_at else None,
            "itens": []
        }

        # Adicionar itens ao dicionário
        for item in pedido.itens:
            item_dict = {
                "id": item.id,
                "id_pedido": item.id_pedido,
                "id_comanda": item.id_comanda,
                "id_produto": item.id_produto,
                "quantidade": item.quantidade,
                "preco_unitario": float(item.preco_unitario),
                "preco_total": float(item.preco_total),
                "observacoes": item.observacoes,
                "status": item.status.value,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None
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
                "mesa_id": pedido.mesa_id,
                "tipo_pedido": pedido.tipo_pedido.value,
                "status_geral_pedido": pedido.status_geral_pedido.value,
                "observacoes_pedido": pedido.observacoes_pedido,
                "motivo_cancelamento": pedido.motivo_cancelamento,
                "created_at": pedido.created_at.isoformat() if pedido.created_at else None,
                "updated_at": pedido.updated_at.isoformat() if pedido.updated_at else None,
                "itens": []
            }

            # Adicionar itens ao dicionário
            for item in pedido.itens:
                item_dict = {
                    "id": item.id,
                    "id_pedido": item.id_pedido,
                    "id_comanda": item.id_comanda,
                    "id_produto": item.id_produto,
                    "quantidade": item.quantidade,
                    "preco_unitario": float(item.preco_unitario),
                    "preco_total": float(item.preco_total),
                    "observacoes": item.observacoes,
                    "status": item.status.value,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None
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

    def _verificar_redis_disponivel(self) -> bool:
        """
        Verifica se o Redis está disponível e acessível.
        """
        try:
            redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                socket_connect_timeout=1,
                socket_timeout=1
            )
            redis_client.ping()
            return True
        except (redis.ConnectionError, redis.TimeoutError):
            return False
        except Exception:
            return False

    async def _notificar_novo_pedido(self, pedido_data: dict):
        """
        Notifica sobre um novo pedido via Redis (pub/sub) para sistemas em tempo real.
        Método de instância da classe PedidoService.
        """
        try:
            # Verificar se Redis está disponível antes de tentar conectar
            if not self._verificar_redis_disponivel():
                logger.info("Redis não disponível. Pulando notificação em tempo real.")
                return

            # Configuração do Redis (ajuste conforme sua configuração)
            redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )

            # Verificar conexão Redis
            try:
                redis_client.ping()
                logger.debug("Conexão Redis estabelecida com sucesso")
            except redis.ConnectionError:
                logger.warning("Redis não está disponível. Notificação em tempo real desabilitada.")
                return
            except Exception as e:
                logger.warning(f"Erro ao conectar com Redis: {e}. Notificação em tempo real desabilitada.")
                return

            # Preparar dados para notificação
            message = {
                "tipo": "novo_pedido",
                "pedido_id": pedido_data.get("id"),
                "comanda_id": pedido_data.get("id_comanda"),
                "timestamp": str(pedido_data.get("created_at")) if pedido_data.get("created_at") else None,
                "status": pedido_data.get("status_geral_pedido"),
                "total_itens": len(pedido_data.get("itens", [])) if pedido_data.get("itens") else 0,
                "observacoes": pedido_data.get("observacoes_pedido")
            }

            # Converter para JSON string
            message_json = json.dumps(message, default=str)

            # Publicar no canal Redis
            channel = "novos_pedidos"
            redis_client.publish(channel, message_json)
            logger.info(f"Notificação de novo pedido publicada no Redis - Pedido ID: {pedido_data.get('id')}")

        except redis.RedisError as e:
            logger.error(f"Erro Redis ao notificar novo pedido: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao notificar novo pedido: {e}")

    async def _notificar_novo_pedido_seguro(self, pedido_data: dict):
        """
        Wrapper seguro que não falha se Redis não estiver disponível.
        """
        try:
            await self._notificar_novo_pedido(pedido_data)
        except Exception as e:
            logger.warning(f"Falha na notificação Redis (não crítico): {e}")

    async def _notificar_atualizacao_status_pedido(self, pedido):
        """
        Notifica sobre atualização de status de pedido via Redis.
        """
        try:
            if not self._verificar_redis_disponivel():
                logger.info("Redis não disponível. Pulando notificação de atualização de status.")
                return

            redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )

            # Preparar dados para notificação
            message = {
                "tipo": "status_pedido_atualizado",
                "pedido_id": pedido.id,
                "comanda_id": pedido.id_comanda,
                "novo_status": pedido.status_geral_pedido.value,
                "timestamp": datetime.now().isoformat()
            }

            message_json = json.dumps(message, default=str)

            # Publicar no canal Redis
            channel = "status_pedidos"
            redis_client.publish(channel, message_json)
            logger.info(f"Notificação de status atualizado publicada - Pedido ID: {pedido.id}")

        except Exception as e:
            logger.warning(f"Erro ao notificar atualização de status (não crítico): {e}")


# Instância do serviço para uso nas rotas
pedido_service = PedidoService()
