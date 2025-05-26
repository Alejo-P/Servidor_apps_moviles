from fastapi import WebSocket, Depends, HTTPException, status
from jwt import PyJWTError as JWTError
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.users_model import User
from app.utils.jwt_handler import verify_token

async def get_current_user_from_ws(websocket: WebSocket, db: Session = Depends(get_db)):
    cookie_header = websocket.headers.get("cookie")
    if not cookie_header:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se encontró la cookie")

    # Buscar el token entre las cookies
    cookies = dict(item.split("=") for item in cookie_header.split("; "))
    token = cookies.get("csrf_access_token")
    
    if not token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token no encontrado en la cookie")

    try:
        payload = verify_token(token, token_type="access")
        user_id = int(payload.get("sub") or 0)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token inválido")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    
    return user
