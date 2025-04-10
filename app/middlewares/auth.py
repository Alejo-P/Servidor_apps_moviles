# app/middlewares/auth.py
from fastapi import Depends, HTTPException, Request
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import RevokedTokenError, MissingTokenError, JWTDecodeError
from sqlalchemy.orm import Session

from app.models.users_model import User
from app.config.database import get_db
from app.config.constants import *

def auth_user(required_roles: list[str]):
    def wrapper(
        Authorize: AuthJWT = Depends(),
        db: Session = Depends(get_db)
    ):
        try:
            Authorize.jwt_required()
            user_id = Authorize.get_jwt_subject()
            user = db.get(User, user_id)
            check_role = True

            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            # Si el rol requerido es "Todos", no se requiere verificación de roles
            if ROLE_ALL in required_roles:
                check_role = False
            
            # Verificar si el usuario tiene alguno de los roles requeridos
            roles = [role.name for role in user.roles]
            if (check_role and not any(role in roles for role in required_roles)):
                raise HTTPException(status_code=403, detail="Permisos insuficientes")

            return user
        except JWTDecodeError:
            raise HTTPException(status_code=401, detail="Token expirado")

        except MissingTokenError:
            raise HTTPException(status_code=401, detail="Token faltante")

        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

    return wrapper

