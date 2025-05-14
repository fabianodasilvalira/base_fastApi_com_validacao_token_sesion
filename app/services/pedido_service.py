# app/services/pedido_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from decimal import Decimal
from typing import List, Optional
import uuid # Para gerar hash de QRCode da comanda, se necessário

from app.models.comanda import Comanda as ComandaModel, StatusComanda
from app.models.item_pedido import ItemPedido as ItemPedidoModel, StatusPedidoItem
from app.models.produto import Produto as ProdutoModel
from app.models.mesa import Mesa as MesaModel # Para obter o número da mesa

from app.schemas.public_pedido_schemas import PedidoPublicCreateSchema, ItemPedidoPublicCreateSchema, PedidoPublicResponseSchema, ItemPedidoPublicResponseSchema
from app.schemas.comanda_schemas import ComandaCreate, ComandaStatus # Supondo que ComandaStatus é o Enum
from app.schemas.item_pedido_schemas import ItemPedidoCreate # Schema interno para criar item_pedido

# Importar outros services que seriam necessários
from app.services import comanda_service, produto_service, item_pedido_service # Estes são placeholders
from app.services.redis_service import redis_service_instance, WebSocketMessage # Para notificações
from app.schemas.websocket_schemas import ComandaStatusUpdatePayload, NotificationPayload # Para notificações

from loguru import logger

async def processar_pedido_publico(
    db: AsyncSession,
    mesa_id: int,
    pedido_public_data: PedidoPublicCreateSchema,
    mesa_numero: Optional[str] = None # Número da mesa para a resposta
) -> PedidoPublicResponseSchema:
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
        # O ID do cliente pode ser nulo inicialmente para pedidos de mesa sem identificação prévia
        # O ID do usuário (funcionário) também pode ser nulo se o pedido é feito pelo cliente
        nova_comanda_data = ComandaCreate(
            id_mesa=mesa_id,
            id_cliente=None, # Cliente pode ser associado depois, ou não, dependendo do fluxo
            id_usuario_abriu=None, # Pedido feito pelo cliente
            status_comanda=StatusComanda.ABERTA, # Ou um status como "AGUARDANDO_CONFIRMACAO"
            observacoes="Comanda aberta via QRCode pelo cliente."
        )
        comanda_ativa = await comanda_service.create_comanda(db, comanda_data=nova_comanda_data)
        if not comanda_ativa:
            logger.error(f"Falha ao criar nova comanda para mesa_id: {mesa_id}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Não foi possível iniciar uma nova comanda para sua mesa.")
        logger.info(f"Nova comanda {comanda_ativa.id} criada para mesa {mesa_id} via QRCode.")
    elif comanda_ativa.status_comanda not in [StatusComanda.ABERTA, StatusComanda.EM_ATENDIMENTO]:
        logger.warning(f"Tentativa de adicionar itens à comanda {comanda_ativa.id} (mesa {mesa_id}) com status {comanda_ativa.status_comanda}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"A comanda atual da mesa não permite novos itens (Status: {comanda_ativa.status_comanda.value}). Chame um garçom.")

    itens_confirmados_response: List[ItemPedidoPublicResponseSchema] = []
    valor_total_novos_itens = Decimal(0)

    # 2. Validar produtos e 3. Adicionar itens à comanda
    if not pedido_public_data.itens:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum item fornecido no pedido.")

    for item_data in pedido_public_data.itens:
        produto = await produto_service.get_produto_by_id(db, item_data.produto_id)
        if not produto:
            logger.warning(f"Produto com ID {item_data.produto_id} não encontrado ao processar pedido para comanda {comanda_ativa.id}")
            # Poderia pular este item e continuar, ou falhar o pedido inteiro.
            # Por segurança, vamos falhar se um item for inválido para evitar confusão.
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Produto com ID {item_data.produto_id} não encontrado no cardápio.")
        
        if not produto.disponivel:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"O produto '{produto.nome}' não está disponível no momento.")

        preco_unitario_item = produto.preco_venda
        preco_total_item_calculado = preco_unitario_item * item_data.quantidade

        novo_item_pedido_data = ItemPedidoCreate(
            id_comanda=comanda_ativa.id,
            id_produto=item_data.produto_id,
            quantidade=item_data.quantidade,
            preco_unitario=preco_unitario_item,
            observacao=item_data.observacao,
            status_pedido_item=StatusPedidoItem.RECEBIDO # Ou "AGUARDANDO_PREPARO"
        )
        # O service item_pedido_service.create_item_pedido deveria salvar e retornar o objeto criado
        item_criado = await item_pedido_service.create_item_pedido(db, item_pedido_data=novo_item_pedido_data)
        if not item_criado:
            logger.error(f"Falha ao criar item_pedido para produto {item_data.produto_id} na comanda {comanda_ativa.id}")
            # Considerar rollback ou tratamento de erro mais robusto aqui
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao adicionar o produto '{produto.nome}' ao seu pedido.")
        
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

    # 4. Recalcular o valor total da comanda e atualizar status (o service da comanda deve fazer isso)
    # Esta chamada pode atualizar comanda_ativa.valor_total_calculado, comanda_ativa.valor_pago, etc.
    comanda_atualizada = await comanda_service.recalculate_comanda_totals_and_update_status(
        db, comanda_id=comanda_ativa.id
    )
    if not comanda_atualizada:
        logger.error(f"Falha ao recalcular totais para comanda {comanda_ativa.id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao finalizar o processamento do seu pedido.")

    # 5. Notificar a equipe sobre o novo pedido/itens
    # Idealmente, a notificação seria mais detalhada, incluindo os itens adicionados.
    mensagem_notificacao_staff = NotificationPayload(
        title="Novo Pedido/Itens Adicionados via QRCode",
        message=f"Mesa {mesa_numero if mesa_numero else mesa_id} adicionou {len(pedido_public_data.itens)} tipo(s) de item(ns) à comanda {comanda_atualizada.id}. Total de novos itens: R$ {valor_total_novos_itens:.2f}.",
        details={"comanda_id": comanda_atualizada.id, "mesa_id": mesa_id, "mesa_numero": mesa_numero, "numero_de_itens_adicionados": len(pedido_public_data.itens)}
    )
    await redis_service_instance.publish_message(
        channel=f"staff_notifications", # Canal geral da equipe
        message=WebSocketMessage(type="notification", payload=mensagem_notificacao_staff.model_dump())
    )
    # Notificar também o canal específico da comanda para atualização em tempo real do cliente (se ele estiver ouvindo)
    # (O payload aqui poderia ser o status completo da comanda ou apenas os novos itens)
    payload_atualizacao_comanda = ComandaStatusUpdatePayload(
        comanda_id=str(comanda_atualizada.id),
        status_comanda=comanda_atualizada.status_comanda.value,
        message=f"{len(pedido_public_data.itens)} item(ns) adicionado(s) à sua comanda."
    )
    await redis_service_instance.publish_message(
        channel=f"comanda_status:{comanda_atualizada.id}",
        message=WebSocketMessage(type="status_update", payload=payload_atualizacao_comanda.model_dump())
    )

    logger.info(f"Pedido processado com sucesso para comanda {comanda_atualizada.id} (Mesa {mesa_id}). {len(itens_confirmados_response)} itens adicionados.")

    # 6. Retornar uma confirmação para o cliente
    return PedidoPublicResponseSchema(
        id_comanda=str(comanda_atualizada.id),
        status_comanda=comanda_atualizada.status_comanda.value,
        mesa_numero=mesa_numero,
        itens_confirmados=itens_confirmados_response,
        valor_total_comanda_atual=comanda_atualizada.valor_total_calculado, # O valor total atualizado da comanda
        mensagem_confirmacao="Seu pedido foi recebido e está sendo processado!",
        qr_code_comanda_hash=comanda_atualizada.qr_code_comanda_hash # Se a comanda tiver um QR próprio
    )

# --- Funções de serviço placeholder que seriam chamadas --- 
# Estas são apenas para ilustrar as dependências. Elas deveriam existir em seus respectivos arquivos de serviço.

class PlaceholderProdutoService:
    async def get_produto_by_id(self, db: AsyncSession, produto_id: int) -> Optional[ProdutoModel]:
        # Lógica para buscar produto no DB
        # Exemplo: return await db.get(ProdutoModel, produto_id)
        logger.debug(f"[PlaceholderProdutoService] Buscando produto ID: {produto_id}")
        # Simular um produto para o fluxo
        if produto_id == 1:
            return ProdutoModel(id=1, nome="Produto Teste 1", preco_venda=Decimal("10.50"), disponivel=True)
        if produto_id == 2:
            return ProdutoModel(id=2, nome="Produto Teste 2", preco_venda=Decimal("20.00"), disponivel=True)
        return None

class PlaceholderItemPedidoService:
    async def create_item_pedido(self, db: AsyncSession, item_pedido_data: ItemPedidoCreate) -> Optional[ItemPedidoModel]:
        # Lógica para criar item_pedido no DB
        logger.debug(f"[PlaceholderItemPedidoService] Criando item_pedido para comanda {item_pedido_data.id_comanda}, produto {item_pedido_data.id_produto}")
        # Simular criação
        return ItemPedidoModel(
            id=uuid.uuid4(), 
            id_comanda=item_pedido_data.id_comanda, 
            id_produto=item_pedido_data.id_produto, 
            quantidade=item_pedido_data.quantidade, 
            preco_unitario_registrado=item_pedido_data.preco_unitario,
            observacao=item_pedido_data.observacao,
            status_pedido_item=item_pedido_data.status_pedido_item
        )

class PlaceholderComandaService:
    _comandas_db = {} # Simulação de DB em memória para comandas

    async def get_active_comanda_by_mesa_id(self, db: AsyncSession, mesa_id: int) -> Optional[ComandaModel]:
        logger.debug(f"[PlaceholderComandaService] Buscando comanda ativa para mesa_id: {mesa_id}")
        for cmd_id, cmd_data in self._comandas_db.items():
            if cmd_data.id_mesa == mesa_id and cmd_data.status_comanda in [StatusComanda.ABERTA, StatusComanda.EM_ATENDIMENTO]:
                return cmd_data
        return None

    async def create_comanda(self, db: AsyncSession, comanda_data: ComandaCreate) -> Optional[ComandaModel]:
        logger.debug(f"[PlaceholderComandaService] Criando comanda para mesa_id: {comanda_data.id_mesa}")
        new_id = len(self._comandas_db) + 1 # Simples ID incremental
        nova_comanda = ComandaModel(
            id=new_id,
            id_mesa=comanda_data.id_mesa,
            status_comanda=comanda_data.status_comanda,
            valor_total_calculado=Decimal(0),
            valor_pago=Decimal(0),
            qr_code_comanda_hash=str(uuid.uuid4()) # Gerar um hash para a comanda
            # ... outros campos de ComandaModel
        )
        self._comandas_db[new_id] = nova_comanda
        return nova_comanda

    async def recalculate_comanda_totals_and_update_status(self, db: AsyncSession, comanda_id: int) -> Optional[ComandaModel]:
        logger.debug(f"[PlaceholderComandaService] Recalculando totais para comanda_id: {comanda_id}")
        if comanda_id not in self._comandas_db:
            return None
        comanda = self._comandas_db[comanda_id]
        # Lógica de recálculo (simulada)
        # Em um caso real, buscaria os ItemPedido associados e somaria os totais.
        # Aqui, vamos apenas simular um aumento no valor total para fins de teste.
        # Supondo que os itens já foram adicionados e o valor_total_calculado reflete isso.
        # Se a comanda estava vazia e agora tem itens, pode mudar o status para EM_ATENDIMENTO
        if comanda.status_comanda == StatusComanda.ABERTA and comanda.valor_total_calculado > 0:
             comanda.status_comanda = StatusComanda.EM_ATENDIMENTO
        # Esta função deveria buscar os itens da comanda no DB e somar seus (preco_unitario * quantidade)
        # comanda.valor_total_calculado = sum_of_item_totals
        return comanda

# Instanciar os placeholders para que o `processar_pedido_publico` possa chamá-los
# Em uma aplicação real, você importaria as instâncias reais dos seus services.
produto_service = PlaceholderProdutoService()
item_pedido_service = PlaceholderItemPedidoService()
comanda_service = PlaceholderComandaService()

# Nota: Este arquivo de serviço é uma estrutura. A lógica real de banco de dados
# e as interações completas com outros serviços precisam ser implementadas
# nos respectivos arquivos de serviço da sua aplicação.

