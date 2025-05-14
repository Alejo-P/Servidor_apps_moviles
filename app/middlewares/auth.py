# app/middlewares/auth_user.py
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from jwt import ExpiredSignatureError, InvalidSignatureError, DecodeError

from app.config.database import get_db
from app.config.settings import settings
from app.models.users_model import User
from app.utils.jwt_handler import verify_token
from app.config.constants import ROLE_ALL

def auth_user(required_roles: list[str]):
    def wrapper(
        request: Request,
        db: Session = Depends(get_db)
    ):
        try:
            token = request.cookies.get("csrf_access_token")
            if not token:
                raise HTTPException(status_code=401, detail="Token faltante")

            payload = verify_token(token)
            user_id = payload.get("sub")

            if not user_id:
                raise HTTPException(status_code=401, detail="Usuario inválido")

            user = db.get(User, int(user_id))
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            if not user.is_active:
                raise HTTPException(status_code=403, detail="Usuario inactivo")

            if not user.is_verified:
                raise HTTPException(status_code=403, detail="Usuario no verificado")

            user_roles = [role.name for role in user.roles]

            if ROLE_ALL in required_roles:
                return user

            if not any(role in user_roles for role in required_roles):
                raise HTTPException(status_code=403, detail="Permisos insuficientes")

            return user

        except ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except (InvalidSignatureError, DecodeError):
            raise HTTPException(status_code=401, detail="Token inválido")
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            else:
                raise HTTPException(status_code=401, detail=str(e))

    return wrapper
