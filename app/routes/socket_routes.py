# app/main.py o app/routes/socket_routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
import json, asyncio

from app.config.database import get_db
from app.models.users_model import User
from app.sockets.websockets import manager
from app.utils.ws_handler import get_current_user_from_ws
from app.config.constants import *

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time communication.
    This endpoint handles user authentication, connection management, and message broadcasting.
    """
    print("🔗 Conexión WebSocket iniciada")

    try:
        user = await get_current_user_from_ws(websocket, db)
        await websocket.accept()

        await manager.connect(
            websocket,
            user_id=user.id,
            roles=[role.name for role in user.roles]
        )
        
        db.query(User).filter(User.id == user.id).update({User.is_connected: True})
        db.commit()
        print(f"✅ Usuario conectado: {user.id}")
        await manager.broadcast({"event": "user_connected", "user_id": user.id}, roles=[ROLE_ADMIN], exclude=[user.id])

        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)
            print("📨 Mensaje recibido:", data_json)
            
    except HTTPException as e:
        print(f"🛑 Error autenticación WS: {e.detail}")
        await websocket.close(code=1008)  # 1008 = Policy Violation

    except WebSocketDisconnect:
        print(f"❌ Usuario desconectado: {user.id}, se esperara 5 segundos antes de marcarlo como desconectado")
        manager.disconnect(websocket)
        
        # Esperar 5 segundos antes de marcar al usuario como desconectado
        await asyncio.sleep(5)
        
        # Verificar si el usuario sigue conectado
        print(manager.debug_active_connections())
        if not manager.is_user_connected(user.id):
            print(f"✅ Usuario desconectado: {user.id}")
            
            # Marcar al usuario como desconectado en la base de datos
            db.query(User).filter(User.id == user.id).update({User.is_connected: False})
            db.commit()
            await manager.broadcast({"event": "user_disconnected", "user_id": user.id}, roles=[ROLE_ADMIN], exclude=[user.id])
        

    except Exception as e:
        print(f"⚠️ Error inesperado: {str(e)}")
        try:
            await websocket.close(code=1011)  # 1011 = Internal Error
        except:
            pass
        
@router.get("/ws/debug")
async def get_ws_state():
    return [
        {
            "user_id": conn.user_id,
            "roles": conn.roles
        }
        for conn in manager.active_connections
    ]
