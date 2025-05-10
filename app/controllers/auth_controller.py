from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Response
from fastapi_jwt_auth.exceptions import RevokedTokenError, MissingTokenError, JWTDecodeError
from sqlalchemy.orm import Session
import cloudinary.uploader
from PIL import Image
import io
import hashlib

from app.config.database import get_db
from app.config.mailer import send_email_background
from app.models.roles_model import Role
from app.models.users_model import User
from app.models.avatarImages_model import AvatarImage
from app.middlewares.auth import auth_user
from app.config.constants import *
from app.config.settings import settings
from app.utils.jwt_handler import create_access_token, create_refresh_token
from app.utils.parse import parse_date
from app.schemas.upload_avatar_schema import AvatarUploadForm
from app.schemas.register_schema import RegisterSchema
from app.schemas.login_schema import LoginSchema
from app.schemas.update_profile_schema import UpdatePasswordSchema, UpdateProfileSchema

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
    response: Response,
    db: Session = Depends(get_db)
):
    """Inicia sesión y devuelve un token de acceso y un token de refresco."""
    user = db.query(User).filter_by(email=data.email).first()
    if not user or not user.check_password(data.password):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="El usuario está inactivo")
    
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="El usuario no está verificado")
    
    # Obtener los roles del usuario y almacenarlas en el token
    roles = [role.name for role in user.roles]
    if not roles:
        raise HTTPException(status_code=403, detail="El usuario no tiene roles asignados")
    
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=int(parse_date(settings.JWT_ACCESS_TOKEN_EXPIRES).total_seconds()),
        secure=True,
        samesite="Lax",
        path="/"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=int(parse_date(settings.JWT_REFRESH_TOKEN_EXPIRES).total_seconds()),
        secure=True,
        samesite="Lax",
        path="/"
    )
    
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
        # Crear el token de acceso con los roles del usuario y entregarlo como cookie
        new_access_token = Authorize.create_access_token(subject=current_user)
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
    Authorize: AuthJWT = Depends()
):
    """Cierra la sesión del usuario."""
    try:
        Authorize.jwt_required()
    except (JWTDecodeError, MissingTokenError):
        pass  # O un log si querés
    
    Authorize.unset_jwt_cookies()
    
    return {"msg": "Sesión cerrada exitosamente"}

@router.get("/profile", status_code=status.HTTP_200_OK) # /api/v1/profile
def profile(
    userInfo: User = Depends(auth_user([ROLE_ALL])),
):
    """Devuelve los datos del perfil del usuario autenticado."""
    return userInfo.to_dict()

@router.put("/profile", status_code=status.HTTP_200_OK) # /api/v1/profile
def update_profile(
    data: UpdateProfileSchema,
    userInfo: User = Depends(auth_user([ROLE_ALL])),
    db: Session = Depends(get_db)
):
    """Actualiza los datos del perfil del usuario autenticado."""
    if db.query(User).filter(User.email == data.email, User.id != userInfo.id).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    userInfo.name = data.name
    userInfo.email = data.email
    db.commit()
    db.refresh(userInfo)
    
    return {
        "msg": "Perfil actualizado exitosamente",
        "user": userInfo.to_dict()
    }
    
@router.put("/profile/update_password", status_code=status.HTTP_200_OK) # /api/v1/profile/update_password   
def change_password(
    data: UpdatePasswordSchema,
    userInfo: User = Depends(auth_user([ROLE_ALL])),
    db: Session = Depends(get_db)
):
    """Cambia la contraseña del usuario autenticado."""    
    if not userInfo.check_password(data.current_password):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    
    # Verificar que la nueva contraseña no sea igual a la actual
    if data.new_password == data.current_password:
        raise HTTPException(status_code=400, detail="La nueva contraseña no puede ser igual a la actual")
    
    # Verificar que la nueva contraseña cumpla con los requisitos
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe tener al menos 8 caracteres")
    
    if not any(char.isdigit() for char in data.new_password):
        raise HTTPException(status_code=400, detail="La nueva contraseña debe contener al menos un número")
    
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")
    
    userInfo.password = data.new_password
    db.commit()
    db.refresh(userInfo)
    
    return {"msg": "Contraseña cambiada exitosamente"}

@router.put("/profile/upload_avatar", status_code=status.HTTP_200_OK)
async def upload_avatar(
    form_data: AvatarUploadForm = Depends(AvatarUploadForm.as_form),
    file: UploadFile = File(...),
    userInfo: User = Depends(auth_user([ROLE_ALL])),
    db: Session = Depends(get_db)
):
    """Sube una imagen de perfil para el usuario autenticado con validaciones."""
    if not file:
        raise HTTPException(status_code=400, detail="No se ha subido ningún archivo")
    
    user_id = userInfo.id
    if not user_id:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")

    try:
        requested_user_id = int(form_data.user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de usuario inválido")

    user_roles = [roles.name for roles in userInfo.roles]
    if ROLE_ADMIN in user_roles:
        user = db.get(User, requested_user_id)
    else:
        if int(user_id) != requested_user_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para cambiar el avatar de otro usuario")
        user = db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Validar el archivo
    try:
        file_content = await file.read()
        
        # Calcular hash de la imagen
        image_hash = hashlib.sha256(file_content).hexdigest()
        
        # Buscar si ya existe ese hash en la base
        existing_avatar = db.query(AvatarImage).filter_by(hash_id=image_hash).first()
        
        if existing_avatar:
            user.avatar_id = existing_avatar.id
            db.commit()
            db.refresh(user)
            return {
                "msg": "Avatar asignado exitosamente (imagen ya existente)",
                "avatar": existing_avatar.to_dict()
            }

        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > settings.MAX_FILE_SIZE_MB:
            raise HTTPException(status_code=400, detail=f"El archivo supera el tamaño máximo permitido de {settings.MAX_FILE_SIZE_MB}MB")

        if file.content_type not in settings.ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=400, detail=f"Tipo de archivo no permitido: {file.content_type}")

        # Validar si es cuadrada
        try:
            image = Image.open(io.BytesIO(file_content))
            if image.width != image.height:
                raise HTTPException(status_code=400, detail="La imagen debe ser cuadrada (mismo ancho y alto)")
        except Exception:
            raise HTTPException(status_code=400, detail="No se pudo analizar la imagen para validar dimensiones")

        file.file.seek(0)

        upload_result = cloudinary.uploader.upload(file.file, folder="avatars")
        new_avatar = AvatarImage(
            url=upload_result["secure_url"],
            public_id=upload_result["public_id"],
            hash_id=image_hash, # Guardamos el hash como identificador local
            format=upload_result["format"],
            width=upload_result.get("width"),
            height=upload_result.get("height")
        )
        db.add(new_avatar)
        db.commit()
        db.refresh(new_avatar)
        
        # Asignar nuevo avatar al usuario
        user.avatar_id = new_avatar.id
        db.commit()
        db.refresh(user)

        return {
            "msg": "Avatar subido exitosamente",
            "avatar": new_avatar.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir avatar: {str(e)}")
