from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Optional
import json
from dataclasses import dataclass

from app.models.users_model import User

@dataclass
class WSConnection:
    websocket: WebSocket
    user_id: int
    roles: List[str]

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WSConnection] = []

    async def connect(self, websocket: WebSocket, user_id: int, roles: List[str]):
        #await websocket.accept()
        self.active_connections.append(
            WSConnection(websocket=websocket, user_id=user_id, roles=roles)
        )
        
    def is_user_connected(self, user_id):
        return any(conn.user_id == user_id for conn in self.active_connections)

    def disconnect(self, websocket: WebSocket):
        self.active_connections = [
            conn for conn in self.active_connections if conn.websocket != websocket
        ]

    async def broadcast(self, message: dict, *, roles: Optional[List[str]] = None, user_id: Optional[int] = None, exclude: List[int] = []):
        data = json.dumps(message)
        print(f"[WS] Enviando mensaje: {data}, a roles: {roles}, user_id: {user_id}, exclude: {exclude}")

        for conn in self.active_connections:
            if conn.user_id in exclude:
                continue
            if roles and not any(role in conn.roles for role in roles):
                continue
            if user_id is not None and conn.user_id != user_id:
                continue
            try:
                print(f"[WS] Enviando a usuario {conn.user_id}")
                await conn.websocket.send_text(data)
            except Exception as e:
                print(f"[WS] Error al enviar a {conn.user_id}: {e}")

manager = ConnectionManager()
