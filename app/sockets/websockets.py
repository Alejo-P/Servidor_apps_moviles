from fastapi import WebSocket
from typing import List, Optional
import json
from dataclasses import dataclass

def _check_send_user(conn, roles_list, include_list, exclude_list):
    print(f"[WS] Evaluando envío a {conn.user_id} con roles {conn.roles}")
    if conn.user_id in exclude_list: return False
    elif roles_list and not any(role in conn.roles for role in roles_list): return False
    elif include_list and conn.user_id not in include_list: return False
    else: return True

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
        
    async def update_conection(self, user_id, roles: List[str]):
        """
        Actualiza los roles de un usuario conectado.
        Si el usuario no está conectado, no hace nada.
        1. Busca la conexión del usuario.
        2. Si la conexión existe, actualiza los roles.
        3. Si no existe, no hace nada.
        """
        for conn in self.active_connections:
            if conn.user_id == user_id:
                conn.roles = roles
                print(f"[WS] Roles actualizados para usuario {user_id}: {roles}")
                return
        print(f"[WS] No se encontró conexión para usuario {user_id}, no se actualizaron roles.")
        print(f"[WS] Conexiones activas: {len(self.active_connections)}")
        print(self.debug_active_connections())

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

    async def broadcast(
        self,
        message: dict,
        *,
        roles: Optional[List[str]] = None,
        exclude: List[int] = [],
        include: List[int] = []
    ):
        """
        Enviar mensaje WebSocket con lógica clara de prioridad:

        - Si `include` tiene usuarios, se les enviará sí o sí.
        - Si `roles` o `user_id` están definidos, se usará para filtrar el resto.
        - `exclude` siempre tiene la última palabra.
        """

        data = json.dumps(message)
        print(f"[WS] Enviando mensaje: {data}")
        print(f"[WS] Enviando a los usuarios con los roles ->", roles, "incluyendo a ->", include, "excluyendo a ->", exclude)
        if not self.active_connections:
            print("[WS] No hay conexiones activas para enviar el mensaje.")
            return
        self.debug_active_connections()

        for conn in self.active_connections:
            should_send = _check_send_user(conn, roles or [], include or [], exclude)
            if should_send:
                try:
                    print(f"[WS] Enviando a usuario {conn.user_id}, con los roles {conn.roles}")
                    await conn.websocket.send_text(data)
                except Exception as e:
                    print(f"[WS] Error al enviar a {conn.user_id}: {e}")

manager = ConnectionManager()
