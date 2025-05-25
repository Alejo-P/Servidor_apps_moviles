# app/main.py o app/routes/socket_routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import json, asyncio

from app.config.database import get_db
from app.models.users_model import User
from app.sockets.websockets import manager
from app.utils.ws_handler import get_current_user_from_ws
from app.config.constants import *

router = APIRouter()

@router.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for notifications.
    """
    print("🔗 Conexión WebSocket iniciada")
    await websocket.accept()

    try:
        user = await get_current_user_from_ws(websocket, db)

        await manager.connect(
            websocket,
            user_id=user.id,
            roles=[role.name for role in user.roles]
        )
        
        db.query(User).filter(User.id == user.id).update({User.is_connected: True})
        db.commit()
        print(f"✅ Usuario conectado: {user.id}")

        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)
            print("📨 Mensaje recibido:", data_json)
            
            if data_json["event"] == "user_connected":
                # Aquí puedes manejar el evento de usuario conectado
                print(f"Usuario conectado: {user.id}")
                await manager.broadcast({"event": "user_connected", "user_id": user.id}, roles=[ROLE_ADMIN], exclude=[user.id])

    except WebSocketDisconnect:
        print(f"❌ Usuario desconectado: {user.id}, se esperara 5 segundos antes de marcarlo como desconectado")
        
        # Esperar 5 segundos antes de marcar al usuario como desconectado
        await asyncio.sleep(5)
        
        # Verificar si el usuario sigue conectado
        if not manager.is_user_connected(user.id):
            print(f"✅ Usuario desconectado: {user.id}")
            
            # Marcar al usuario como desconectado en la base de datos
            db.query(User).filter(User.id == user.id).update({User.is_connected: False})
            db.commit()
        
        manager.disconnect(websocket)
        print(f"🔌 Desconectando WebSocket del usuario: {user.id}")
        await manager.broadcast({"event": "user_disconnected", "user_id": user.id}, roles=[ROLE_ADMIN], exclude=[user.id])

    except Exception as e:
        print("⚠️ Error en WebSocket:", str(e))
        try:
            await websocket.close(code=1008)
        except Exception as close_error:
            print(f"WS close falló: {close_error}")