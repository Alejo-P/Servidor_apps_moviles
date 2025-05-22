# app/main.py o app/routes/socket_routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.sockets.websockets import manager
from app.utils.ws_handler import get_current_user_from_ws

router = APIRouter()

@router.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()

    try:
        user = await get_current_user_from_ws(websocket, db)

        await manager.connect(
            websocket,
            user_id=user.id,
            roles=[role.name for role in user.roles]
        )

        while True:
            await websocket.receive_text()  # o procesás lo que necesites

    except WebSocketDisconnect:
        manager.disconnect(websocket)

    except Exception as e:
        print("Error en WebSocket:", str(e))
        await websocket.close()