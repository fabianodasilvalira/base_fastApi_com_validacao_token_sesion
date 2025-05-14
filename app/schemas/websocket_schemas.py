# app/schemas/websocket_schemas.py
from pydantic import BaseModel
from typing import Any, Literal, Optional

class WebSocketMessage(BaseModel):
    type: Literal["notification", "status_update", "error", "info"]
    payload: Any
    target_user_id: Optional[str] = None # Para mensagens direcionadas
    target_role: Optional[Literal["staff", "client"]] = None # Para mensagens a grupos
    comanda_id: Optional[str] = None # Para filtrar atualizações de comanda
    mesa_id: Optional[str] = None # Para filtrar atualizações de mesa

class NotificationPayload(BaseModel):
    title: str
    message: str
    details: Optional[dict] = None

class ComandaStatusUpdatePayload(BaseModel):
    comanda_id: str
    status_comanda: str # Usar o Enum StatusComanda do comanda_schemas
    item_id: Optional[str] = None # Se a atualização for de um item específico
    status_item: Optional[str] = None # Usar o Enum StatusPedido do item_pedido
    message: Optional[str] = None

class ClientCallStaffPayload(BaseModel):
    mesa_id: str
    mesa_numero: str
    message: str = "Cliente solicitando atendimento."

