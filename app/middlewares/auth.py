from fastapi import Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import MissingTokenError, JWTDecodeError

from app.config.constants import ROLE_ALL

def auth_user(required_roles: list[str]):
    def wrapper(Authorize: AuthJWT = Depends()):
        try:
            Authorize.jwt_required()
            user_id = Authorize.get_jwt_subject()
            claims = Authorize.get_raw_jwt()
            user_roles = claims.get("roles", [])

            if not user_id:
                raise HTTPException(status_code=401, detail="Usuario inválido")

            # Si se permite cualquier rol, se omite la verificación
            if ROLE_ALL in required_roles:
                return {"id": user_id, "roles": user_roles}

            # Verificar si tiene algún rol permitido
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(status_code=403, detail="Permisos insuficientes")

            return {"user_id": user_id, "roles": user_roles}

        except MissingTokenError:
            raise HTTPException(status_code=401, detail="Token faltante")
        except JWTDecodeError:
            raise HTTPException(status_code=401, detail="Token inválido o expirado")
        except Exception as e:
            raise HTTPException(status_code=401, detail=e.message if hasattr(e, 'message') else str(e))

    return wrapper
