from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import RevokedTokenError, MissingTokenError, JWTDecodeError
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.roles_model import Role
from app.models.users_model import User
from app.middlewares.auth import auth_user
from app.middlewares.auth_user_db import auth_user_db
from app.config.constants import *
from app.schemas.register_schema import RegisterSchema
from app.schemas.login_schema import LoginSchema
from app.schemas.role_user_schema import RoleUserSchema

# Crear el router para la autenticación
router = APIRouter()
    
@router.post("/register", status_code=status.HTTP_201_CREATED)  # /api/v1/register
def register(
    data: RegisterSchema,
    db: Session = Depends(get_db),
):
    """Registra un nuevo usuario en la base de datos."""
    if db.query(User).filter_by(email=data.email).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    role = db.query(Role).filter_by(name="Usuario").first()
    if not role:
        raise HTTPException(status_code=500, detail="Rol 'Usuario' no encontrado")
    
    user = User(name=data.name, email=data.email, password=data.password)
    user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"msg": "Usuario registrado exitosamente"}

@router.post("/login", status_code=status.HTTP_200_OK)  # /api/v1/login
def login(
    data: LoginSchema,
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends()
):
    """Inicia sesión y devuelve un token de acceso y un token de refresco."""
    user = db.query(User).filter_by(email=data.email).first()
    if not user or not user.check_password(data.password):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    
    # Obtener los roles del usuario y almacenarlas en el token
    roles = [role.name for role in user.roles]
    print("Roles -> ",roles)
    access_token = Authorize.create_access_token(subject=str(user.id), user_claims={"roles": roles})
    refresh_token = Authorize.create_refresh_token(subject=str(user.id), user_claims={"roles": roles})

    Authorize.set_access_cookies(access_token)
    Authorize.set_refresh_cookies(refresh_token)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "msg": "Inicio de sesión exitoso"
    }

@router.post("/refresh", status_code=status.HTTP_200_OK)  # /api/v1/refresh
def refresh_token(Authorize: AuthJWT = Depends()):
    """Refresca el token de acceso usando el token de refresco."""
    try:
        Authorize.jwt_refresh_token_required()
        current_user = Authorize.get_jwt_subject()
        user_claims = Authorize.get_raw_jwt()
        roles = user_claims.get("roles", [])
        # Crear el token de acceso con los roles del usuario y entregarlo como cookie
        new_access_token = Authorize.create_access_token(subject=current_user, user_claims={"roles": roles})
        Authorize.set_access_cookies(new_access_token)
        return {"access_token": new_access_token}
    except RevokedTokenError:
        raise HTTPException(status_code=401, detail="Refresh token revocado")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# @router.get("/active_sessions", status_code=status.HTTP_200_OK)  # /api/v1/active_sessions
# def active_sessions(
#     Authorize: AuthJWT = Depends(),
#     db: Session = Depends(get_db)
# ):
#     """Devuelve las sesiones activas del usuario."""
#     Authorize.jwt_required()
#     user_id = int(Authorize.get_jwt_subject())

#     tokens = db.query(RefreshToken).filter(
#         RefreshToken.user_id == user_id,
#         RefreshToken.is_active == True,
#         RefreshToken.expires_at > datetime.utcnow()
#     ).all()
    
#     return JSONResponse(status_code=200, content={
#         "active_sessions": [token.to_dict() for token in tokens]
#     })

@router.post("/logout", status_code=status.HTTP_200_OK) # /api/v1/logout
def logout(
    Authorize: AuthJWT = Depends(auth_user([ROLE_ALL]))
):
    """Cierra la sesión del usuario."""
    Authorize.jwt_required()
    Authorize.unset_jwt_cookies()
    
    return {"msg": "Sesión cerrada exitosamente"}

@router.get("/profile", status_code=status.HTTP_200_OK) # /api/v1/profile
def profile(
    user: User = Depends(auth_user_db([ROLE_ALL])),
):
    """Devuelve los datos del perfil del usuario autenticado."""
    return user.to_dict()
    
@router.get("/profile/{user_id}", status_code=status.HTTP_200_OK) # /api/v1/profile/<user_id>
def get_user_profile(
    user_id: int,
    userInfo: dict = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Devuelve los datos del perfil de un usuario específico."""
    try:
        user = db.query(User).get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return {"user": user.to_dict()}
    except (JWTDecodeError, MissingTokenError) as e:
        raise HTTPException(status_code=401, detail="Token inválido o faltante")
    
@router.post("/add_role", status_code=status.HTTP_200_OK) # /api/v1/add_role
def add_role_to_user(
    data: RoleUserSchema,
    userInfo: dict = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Agrega un rol a un usuario."""
    try:
        user = db.query(User).get(data.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        role = db.query(Role).filter_by(name=data.role_name).first()
        if not role:
            raise HTTPException(status_code=404, detail="Rol no encontrado")
        
        # Verificar si el rol ya está asignado al usuario
        if role in user.roles:
            raise HTTPException(status_code=400, detail="El rol ya está asignado al usuario")
        
        user.roles.append(role)
        db.commit()
        db.refresh(user)
        
        return {"msg": "Rol agregado exitosamente"}
    except (JWTDecodeError, MissingTokenError) as e:
        raise HTTPException(status_code=401, detail="Token inválido o faltante")

@router.delete("/remove_role", status_code=status.HTTP_200_OK) # /api/v1/remove_role
def remove_role_from_user(
    data: RoleUserSchema,
    userInfo: dict = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Elimina un rol de un usuario."""
    try:
        user = db.query(User).get(data.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        role = db.query(Role).filter_by(name=data.role_name).first()
        if not role:
            raise HTTPException(status_code=404, detail="Rol no encontrado")
        
        # Verificar si el rol ya ha sido removido del usuario
        if role not in user.roles:
            raise HTTPException(status_code=400, detail="El rol no está asignado al usuario")
        
        # Verificar si el usuario tiene al menos un rol asignado
        if len(user.roles) <= 1:
            raise HTTPException(status_code=400, detail="El usuario debe tener al menos un rol asignado")
        
        user.roles.remove(role)
        db.commit()
        db.refresh(user)
        
        return {"msg": "Rol eliminado exitosamente"}
    except (JWTDecodeError, MissingTokenError) as e:
        raise HTTPException(status_code=401, detail="Token inválido o faltante")