# app/api/v1/websocket_routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from typing import List, Dict, Set
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json
from loguru import logger

from app.core.session import get_db_session
from app.services.redis_service import redis_service_instance
from app.schemas.websocket_schemas import WebSocketMessage, ClientCallStaffPayload, ComandaStatusUpdatePayload
from app.services import comanda_service, mesa_service # Para validar hashes e obter dados

router = APIRouter(prefix="/ws", tags=["WebSockets"])

class ConnectionManager:
    def __init__(self):
        # Conexões ativas: { "canal_ou_id_unico": {websocket1, websocket2} }
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel_id: str):
        await websocket.accept()
        if channel_id not in self.active_connections:
            self.active_connections[channel_id] = set()
        self.active_connections[channel_id].add(websocket)
        logger.info(f"WebSocket conectado ao canal: {channel_id}. Total de conexões no canal: {len(self.active_connections[channel_id])}")

    def disconnect(self, websocket: WebSocket, channel_id: str):
        if channel_id in self.active_connections:
            self.active_connections[channel_id].remove(websocket)
            if not self.active_connections[channel_id]: # Se o canal ficar vazio, remove o canal
                del self.active_connections[channel_id]
            logger.info(f"WebSocket desconectado do canal: {channel_id}.")
        else:
            logger.warning(f"Tentativa de desconectar WebSocket de um canal inexistente ou já vazio: {channel_id}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_to_channel(self, message: str, channel_id: str):
        if channel_id in self.active_connections:
            living_connections = set()
            for connection in self.active_connections[channel_id]:
                try:
                    await connection.send_text(message)
                    living_connections.add(connection)
                except WebSocketDisconnect:
                    logger.info(f"WebSocket desconectado (durante broadcast) do canal: {channel_id}")
                except Exception as e:
                    logger.error(f"Erro ao enviar mensagem para WebSocket no canal {channel_id}: {e}")
                    # Pode ser necessário remover a conexão aqui também se o erro for persistente
            self.active_connections[channel_id] = living_connections
            if not self.active_connections[channel_id]:
                 del self.active_connections[channel_id]

manager = ConnectionManager()

# Canal para notificações da equipe (staff)
STAFF_NOTIFICATION_CHANNEL = "staff_notifications"

# Função para escutar o Redis e transmitir para WebSockets
async def redis_listener_task(channel_pattern: str, target_manager_channel_prefix: str = ""):
    pubsub = None
    while True: # Loop para tentar reconectar em caso de falha
        try:
            pubsub = await redis_service_instance.subscribe_to_channel(channel_pattern)
            if not pubsub:
                logger.error(f"Não foi possível se inscrever no canal Redis {channel_pattern}. Tentando novamente em 10s.")
                await asyncio.sleep(10)
                continue
            
            logger.info(f"Escutando canal Redis: {channel_pattern} para transmitir via WebSocket")
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    logger.debug(f"Mensagem recebida do Redis no canal {message['channel']}: {message['data']}")
                    try:
                        # A mensagem do Redis já deve ser um JSON string de WebSocketMessage
                        data_json = message["data"]
                        # O canal de destino do WebSocket pode ser o mesmo do Redis ou um prefixado
                        ws_channel_id = f"{target_manager_channel_prefix}{message['channel']}"
                        await manager.broadcast_to_channel(data_json, ws_channel_id)
                    except json.JSONDecodeError:
                        logger.error(f"Erro ao decodificar JSON da mensagem do Redis: {message['data']}")
                    except Exception as e:
                        logger.error(f"Erro ao processar mensagem do Redis para WebSocket: {e}")
                await asyncio.sleep(0.01) # Pequena pausa para não sobrecarregar
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Conexão com Redis perdida no listener para {channel_pattern}: {e}. Tentando reconectar em 10s.")
            if pubsub: # Tenta limpar o pubsub antigo
                try: await pubsub.close()
                except: pass
            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"Erro inesperado no listener Redis para {channel_pattern}: {e}. Tentando reiniciar em 10s.")
            if pubsub: 
                try: await pubsub.close()
                except: pass
            await asyncio.sleep(10)

# Iniciar a tarefa de escuta do Redis para notificações da equipe em background
# Isso normalmente seria feito no startup da aplicação FastAPI
# asyncio.create_task(redis_listener_task(STAFF_NOTIFICATION_CHANNEL, target_manager_channel_prefix=""))
# asyncio.create_task(redis_listener_task("comanda_status:*", target_manager_channel_prefix="")) # Para status de comandas

@router.websocket("/staff/notifications")
async def staff_notifications_ws(websocket: WebSocket):
    await manager.connect(websocket, STAFF_NOTIFICATION_CHANNEL)
    # Envia uma mensagem de boas-vindas ou status inicial se necessário
    welcome_message = WebSocketMessage(type="info", payload={"message": "Conectado ao canal de notificações da equipe."})
    await manager.send_personal_message(welcome_message.model_dump_json(), websocket)
    try:
        while True:
            # Apenas mantém a conexão aberta para receber broadcasts do Redis via manager
            # Poderia receber mensagens do staff também, se necessário (ex: confirmação de leitura)
            data = await websocket.receive_text() # Bloqueia até receber algo ou desconectar
            logger.debug(f"Mensagem recebida no WebSocket da equipe (não esperado): {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, STAFF_NOTIFICATION_CHANNEL)
    except Exception as e:
        logger.error(f"Erro no WebSocket da equipe: {e}")
        manager.disconnect(websocket, STAFF_NOTIFICATION_CHANNEL)

@router.websocket("/comanda/{comanda_identificador}/status")
async def comanda_status_ws(websocket: WebSocket, comanda_identificador: str, db: AsyncSession = Depends(get_db_session)):
    # comanda_identificador pode ser o ID numérico ou o qr_code_comanda_hash
    # Precisa validar e obter o ID canônico da comanda para usar como channel_id
    comanda = None
    if comanda_identificador.isdigit():
        comanda = await comanda_service.get_comanda_by_id(db, int(comanda_identificador))
    else:
        comanda = await comanda_service.get_comanda_by_qr_hash(db, comanda_identificador) # Supõe este método no service

    if not comanda:
        logger.warning(f"Tentativa de conexão WebSocket para comanda inválida/não encontrada: {comanda_identificador}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    channel_id = f"comanda_status:{comanda.id}" # Usar ID da comanda como parte do canal
    await manager.connect(websocket, channel_id)
    
    # Envia o status atual da comanda ao conectar
    # (O service precisaria de um método para buscar o status formatado)
    # current_status_payload = await comanda_service.get_formatted_comanda_status_for_ws(db, comanda.id)
    # if current_status_payload:
    #    initial_status_msg = WebSocketMessage(type="status_update", payload=current_status_payload)
    #    await manager.send_personal_message(initial_status_msg.model_dump_json(), websocket)
    # else:
    initial_info_msg = WebSocketMessage(type="info", payload={"message": f"Conectado ao canal de status da comanda {comanda.id}."})
    await manager.send_personal_message(initial_info_msg.model_dump_json(), websocket)

    try:
        while True:
            # Apenas mantém a conexão aberta para receber broadcasts do Redis via manager
            data = await websocket.receive_text() # Bloqueia até receber algo ou desconectar
            logger.debug(f"Mensagem recebida no WebSocket da comanda {comanda.id} (não esperado): {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel_id)
    except Exception as e:
        logger.error(f"Erro no WebSocket da comanda {comanda.id}: {e}")
        manager.disconnect(websocket, channel_id)

# É crucial que as tarefas de escuta do Redis (redis_listener_task)
# sejam iniciadas no evento de startup da aplicação FastAPI.
# Exemplo em main.py:
# from contextlib import asynccontextmanager
# from app.api.v1.websocket_routes import redis_listener_task, STAFF_NOTIFICATION_CHANNEL
#
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup
#     asyncio.create_task(redis_listener_task(STAFF_NOTIFICATION_CHANNEL))
#     asyncio.create_task(redis_listener_task("comanda_status:*")) # Para status de comandas
#     logger.info("Tarefas de escuta do Redis iniciadas.")
#     yield
#     # Shutdown
#     await redis_service_instance.close_redis_client()
#     logger.info("Conexão com Redis fechada.")
#
# app = FastAPI(lifespan=lifespan, ...)

