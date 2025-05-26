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
        await self.disconnect_by_user(user_id)

        connection = WSConnection(websocket, user_id=user_id, roles=roles)
        self.active_connections.append(connection)
        print(f"[WS] Conexión añadida para usuario {user_id}")

    async def disconnect_by_user(self, user_id):
        # Cierra y elimina conexiones existentes de ese usuario
        for conn in self.active_connections[:]:  # copia segura
            if conn.user_id == user_id:
                try:
                    await conn.websocket.close()
                except:
                    pass
                self.active_connections.remove(conn)
        
    def is_user_connected(self, user_id):
        return any(conn.user_id == user_id for conn in self.active_connections)
    
    def debug_active_connections(self):
        print("=== CONEXIONES ACTIVAS ===")
        for conn in self.active_connections:
            print(f"Usuario: {conn.user_id}, Roles: {conn.roles}")
        print("==========================")

    def disconnect(self, websocket: WebSocket):
        self.active_connections = [
            conn for conn in self.active_connections if conn.websocket != websocket
        ]
        if websocket.client:
            print(f"[WS] Conexión cerrada para {websocket.client.host}")
        else:
            print(f"[WS] Se cerró una conexión")
        
        print(f"[WS] Conexiones activas: {len(self.active_connections)}")
        print(self.debug_active_connections())

    async def broadcast(self, message: dict, *, roles: Optional[List[str]] = None, user_id: Optional[int] = None, exclude: List[int] = [], include: List[int] = []):
        """
        Enviar un mensaje a los usuarios conectados con opciones avanzadas:\n
        - Si `include` está presente, solo se envía a esos user_id.
        - Si no, se puede filtrar por roles o por un user_id específico.
        :param message: El mensaje a enviar (como dict).
        :param roles: Lista de roles que deben tener los usuarios para recibir el mensaje.
        :param user_id: Si se especifica, solo se enviará al usuario con este ID.
        :param exclude: Lista de IDs de usuarios a excluir del envío.
        :param include: Lista de IDs de usuarios a incluir en el envío (ignora roles y user_id).
        """
        data = json.dumps(message)
        print(f"[WS] Enviando mensaje: {data}")
        self.debug_active_connections()

        for conn in self.active_connections:
            # Si hay lista "include", solo enviamos a quienes están ahí (y no estén excluidos)
            if include:
                if conn.user_id not in include or conn.user_id in exclude:
                    continue
            else:
                # Si no está en include, aplica filtros normales
                if conn.user_id in exclude:
                    continue
                if user_id is not None and conn.user_id != user_id:
                    continue
                if roles and not any(role in conn.roles for role in roles):
                    continue

            try:
                print(f"[WS] Enviando a usuario {conn.user_id}")
                await conn.websocket.send_text(data)
            except Exception as e:
                print(f"[WS] Error al enviar a {conn.user_id}: {e}")

manager = ConnectionManager()
