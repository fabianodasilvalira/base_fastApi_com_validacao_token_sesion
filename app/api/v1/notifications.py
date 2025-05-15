# app/api/v1/notifications.py
from fastapi import APIRouter, WebSocket
from app.core.notifications import manager

router = APIRouter()

@router.websocket("/ws/notificacao")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Apenas para manter conexão ativa
    except:
        manager.disconnect(websocket)
