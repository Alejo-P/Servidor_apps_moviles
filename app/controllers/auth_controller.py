from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.roles_model import Role
from app.models.token_model import RefreshToken
from app.models.users_model import User
from pydantic import BaseModel

# Crear el router para la autenticación
router = APIRouter()

# Configuracin de esquemas
class RegisterSchema(BaseModel):
    name: str
    email: str
    password: str

class LoginSchema(BaseModel):
    email: str
    password: str

class RefreshSchema(BaseModel):
    refresh_token: str

@router.post("/register", status_code=status.HTTP_200_OK)  # /api/v1/register
def register(
    data: RegisterSchema,
    db: Session = Depends(get_db),
):
    """Registra un nuevo usuario en la base de datos."""
    if db.query(User).filter_by(email=data.email).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    user = User(name=data.name, email=data.email, password=data.password)
    role = db.query(Role).filter_by(name="Usuario").first()
    if not role:
        raise HTTPException(status_code=500, detail="Rol 'Usuario' no encontrado")
    
    user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return JSONResponse(status_code=200, content={"msg": "Usuario registrado exitosamente"})

@router.post("/login", status_code=status.HTTP_200_OK)  # /api/v1/login
def login(
    data: LoginSchema,
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends()
):
    """Inicia sesión y devuelve un token de acceso y un token de refresco."""
    user = db.query(User).filter_by(email=data.email).first()
    if not user or not user.check_password(data.password):
        raise HTTPException(status_code=400, detail="Email o contraseña incorrectos")

    roles = [role.name for role in user.roles]
    additional_claims = {"roles": roles}
    
    access_token = Authorize.create_access_token(subject=str(user.id), user_claims=additional_claims)
    refresh_token = Authorize.create_refresh_token(subject=str(user.id))

    db.add(RefreshToken(token=refresh_token, user_id=user.id))
    db.commit()
    
    return JSONResponse(status_code=200, content={
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict()
    })

@router.post("/refresh", status_code=status.HTTP_200_OK)  # /api/v1/refresh
def refresh(
    data: RefreshSchema,
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends()
):
    """Refresca el token de acceso."""
    token_db = db.query(RefreshToken).filter_by(token=data.refresh_token, is_active=True).first()
    if not token_db:
        raise HTTPException(status_code=400, detail="Token de refresco inválido")

    user = db.query(User).get(token_db.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    roles = [role.name for role in user.roles]
    additional_claims = {"roles": roles}

    new_access_token = Authorize.create_access_token(subject=str(user.id), user_claims=additional_claims)
    
    # Actualizar el token de refresco en la base de datos
    return JSONResponse(status_code=200, content={
        "access_token": new_access_token,
        "refresh_token": token_db.token,
        "user": user.to_dict()
    })

@router.get("/active_sessions", status_code=status.HTTP_200_OK)  # /api/v1/active_sessions
def active_sessions(
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db)
):
    """Devuelve las sesiones activas del usuario."""
    Authorize.jwt_required()
    user_id = int(Authorize.get_jwt_subject())

    tokens = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_active == True,
        RefreshToken.expires_at > datetime.utcnow()
    ).all()
    
    return JSONResponse(status_code=200, content={
        "active_sessions": [token.to_dict() for token in tokens]
    })

@router.post("/logout") # /api/v1/logout
def logout(
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db)
):
    """Cierra la sesión del usuario."""
    Authorize.jwt_required()
    user_id = int(Authorize.get_jwt_subject())

    token = db.query(RefreshToken).filter_by(user_id=user_id, is_active=True).first()
    if not token:
        raise HTTPException(status_code=400, detail="No hay sesión activa")

    db.delete(token)
    db.commit()
    Authorize.unset_jwt_cookies()
    
    return JSONResponse(status_code=200, content={"msg": "Sesión cerrada exitosamente"})

@router.get("/profile", status_code=status.HTTP_200_OK) # /api/v1/profile
def profile(
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db)
):
    """Devuelve los datos del perfil del usuario autenticado."""
    Authorize.jwt_required()
    user_id = int(Authorize.get_jwt_subject())

    user = db.query(User).get(user_id)

    return JSONResponse(status_code=200, content={
        "user": user.to_dict()
    })

@router.get("/profile/{user_id}") # /api/v1/profile/<user_id>
def get_user_profile(
    user_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db)
):
    """Devuelve los datos del perfil de un usuario específico."""
    Authorize.jwt_required()
    claims = Authorize.get_raw_jwt()
    
    if "roles" not in claims or "admin" not in claims["roles"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para acceder a este recurso")

    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return JSONResponse(status_code=200, content={
        "user": user.to_dict()
    })