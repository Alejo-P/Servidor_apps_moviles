# app/middlewares/auth_user_db.py
from fastapi import Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import MissingTokenError, JWTDecodeError
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.users_model import User
from app.config.constants import ROLE_ALL

def auth_user_db(required_roles: list[str]):
    def wrapper(
        Authorize: AuthJWT = Depends(),
        db: Session = Depends(get_db)
    ):
        try:
            Authorize.jwt_required()
            user_id = Authorize.get_jwt_subject()

            if not user_id:
                raise HTTPException(status_code=401, detail="Usuario inválido")

            user = db.get(User, int(user_id))
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            user_roles = [role for role in user.roles]

            if ROLE_ALL in required_roles:
                return user

            if not any(role in user_roles for role in required_roles):
                raise HTTPException(status_code=403, detail="Permisos insuficientes")

            return user

        except MissingTokenError:
            raise HTTPException(status_code=401, detail="Token faltante")
        except JWTDecodeError:
            raise HTTPException(status_code=401, detail="Token inválido o expirado")
        except Exception as e:
            raise HTTPException(status_code=401, detail=e.message if hasattr(e, 'message') else str(e))
    
    return wrapper
