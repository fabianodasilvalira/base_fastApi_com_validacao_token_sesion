# app/services/redis_service.py
import redis.asyncio as redis
import json
from typing import Any, Optional
from app.core.config.settings import settings # Supondo que settings.REDIS_URL exista
from app.schemas.websocket_schemas import WebSocketMessage
from loguru import logger

class RedisService:
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self._redis_client: Optional[redis.Redis] = None

    async def get_redis_client(self) -> redis.Redis:
        if self._redis_client is None or not self._redis_client.is_connected:
            try:
                self._redis_client = await redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
                await self._redis_client.ping() # Verificar conexão
                logger.info("Conectado ao Redis com sucesso.")
            except Exception as e:
                logger.error(f"Falha ao conectar ao Redis: {e}")
                # Em um cenário real, poderia tentar reconectar ou levantar uma exceção crítica
                # Por agora, vamos permitir que falhe e as operações subsequentes também falharão.
                self._redis_client = None # Garante que não tentaremos usar um cliente falho
                raise # Re-levanta a exceção para que o chamador saiba da falha
        return self._redis_client

    async def publish_message(self, channel: str, message: WebSocketMessage):
        client = await self.get_redis_client()
        if not client:
            logger.error("Cliente Redis não disponível. Não foi possível publicar a mensagem.")
            return
        try:
            await client.publish(channel, message.model_dump_json())
            logger.info(f"Mensagem publicada no canal {channel}: {message.type}")
        except Exception as e:
            logger.error(f"Erro ao publicar mensagem no Redis no canal {channel}: {e}")

    async def subscribe_to_channel(self, channel: str):
        client = await self.get_redis_client()
        if not client:
            logger.error("Cliente Redis não disponível. Não foi possível inscrever-se no canal.")
            return None # Ou levantar uma exceção
        
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)
        logger.info(f"Inscrito no canal Redis: {channel}")
        return pubsub

    async def close_redis_client(self):
        if self._redis_client and self._redis_client.is_connected:
            await self._redis_client.close()
            logger.info("Conexão com Redis fechada.")
            self._redis_client = None

# Instância global do serviço Redis para ser usada na aplicação
redis_service_instance = RedisService()

async def get_redis_service() -> RedisService:
    # Esta função pode ser usada como uma dependência do FastAPI se necessário,
    # embora a instância global seja frequentemente suficiente para serviços.
    return redis_service_instance

# Exemplo de como usar:
# from app.services.redis_service import redis_service_instance
# await redis_service_instance.publish_message("canal_de_teste", WebSocketMessage(type="info", payload={"data": "Olá Mundo"}))

