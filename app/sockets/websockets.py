from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[Dict] = []

    async def connect(self, websocket: WebSocket, user_id: int, roles: List[str]):
        await websocket.accept()
        self.active_connections.append({
            "websocket": websocket,
            "user_id": user_id,
            "roles": roles
        })

    def disconnect(self, websocket: WebSocket):
        self.active_connections = [
            conn for conn in self.active_connections if conn["websocket"] != websocket
        ]

    async def broadcast(self, message: dict, *, roles: List[str] = [], user_id: int | None = None):
        data = json.dumps(message)
        for conn in self.active_connections:
            if roles and not any(role in conn["roles"] for role in roles):
                continue
            if user_id and conn["user_id"] != user_id:
                continue
            await conn["websocket"].send_text(data)

manager = ConnectionManager()
