from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Response, Request
from sqlalchemy.orm import Session
from urllib.parse import quote
import cloudinary.uploader
from PIL import Image
import io
import hashlib
import jwt

from app.config.constants import *
from app.config.database import get_db
from app.config.mailer import send_email_background
from app.config.settings import settings
from app.middlewares.auth import auth_user
from app.models.avatarImages_model import AvatarImage
from app.models.refresh_token_model import RefreshToken
from app.models.roles_model import Role
from app.models.users_model import User
from app.schemas.login_schema import LoginSchema
from app.schemas.register_schema import RegisterSchema
from app.schemas.update_profile_schema import UpdatePasswordSchema, UpdateProfileSchema
from app.schemas.upload_avatar_schema import AvatarUploadForm
from app.utils.jwt_handler import create_access_token, create_refresh_token, verify_token
from app.utils.parse import parse_date
from app.utils.ua_parser import get_device_info
from app.utils.verif_token import verify_secure_token, create_secure_token
from app.sockets.websockets import manager

# Crear el router para la autenticación
router = APIRouter()
    
@router.post("/register", status_code=status.HTTP_201_CREATED, tags=["Auth Routes"])  # /api/v1/register
def register(
    data: RegisterSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    request: Request = None
):
    """Registra un nuevo usuario en la base de datos."""
    if db.query(User).filter_by(email=data.email).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    role = db.query(Role).filter_by(name=ROLE_USER).first()
    if not role:
        raise HTTPException(status_code=500, detail=f"Rol '{ROLE_USER}' no encontrado")
    
    user = User(name=data.name, email=data.email, password=data.password)
    user.roles.append(role)
    
    # Crear el token de verificación
    token = create_secure_token(settings.SECRET_KEY, str(user.email))
    user.token = token
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Enviar correo de verificación
    send_email_background(
        request,
        background_tasks,
        subject="Verificación de cuenta",
        email_to=str(user.email),
        template_name="verify_email.html",
        body={
            "username": user.name,
            "verify_url": f"{settings.URL_FRONTEND}/#/?verify-email=true&token={quote(token)}",
            "year": settings.CURRENT_TIME.year
        }
    )
    
    return {
        "msg": "Usuario registrado exitosamente",
        "user": user.to_dict()
    }


@router.post("/verify-email/{token}", status_code=status.HTTP_200_OK, tags=["Auth Routes"])  # /api/v1/verify-email/<token>
def verify_email(
    token: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    request: Request = None
):
    payload = verify_secure_token(settings.SECRET_KEY, token)
    if not payload:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    user = db.query(User).filter_by(email=payload["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    print(f"Token: {token}", f"User token: {user.token}")
    
    if not user.token or user.token != token:
        raise HTTPException(status_code=400, detail="Token no coincide con el usuario")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="El usuario no está inactivo")
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="El correo ya ha sido verificado")

    user.is_verified = True
    user.token = None  # Limpiar el token después de la verificación
    db.commit()
    db.refresh(user)
    
    # Enviar correo de confirmación de verificación
    send_email_background(
        request,
        background_tasks,
        subject="Verificación de cuenta exitosa",
        email_to=user.email,
        template_name="verify_email_success.html",
        body={
            "username": user.name,
            "login_url": f"{settings.URL_FRONTEND}/#/?login=true",
            "year": settings.CURRENT_TIME.year
        }
    )

    return {"msg": "Correo verificado exitosamente"}


@router.post("/login", status_code=status.HTTP_200_OK, tags=["Auth Routes"])  # /api/v1/login
async def login(
    data: LoginSchema,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
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
    
    # Obtener los roles del usuario
    roles = [role.name for role in user.roles]
    if not roles:
        raise HTTPException(status_code=403, detail="El usuario no tiene roles asignados")
    
    if data.is_panel_admin and ROLE_ADMIN not in roles:
        raise HTTPException(status_code=403, detail="El usuario no tiene permisos de administrador")

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    device_info = get_device_info(request)

    # Guardar el token de refresco en la base de datos
    refresh_token_db = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_in=parse_date(settings.JWT_REFRESH_TOKEN_EXPIRES),
        device_info=device_info
    )
    db.add(refresh_token_db)
    db.commit()
    db.refresh(refresh_token_db)
    
    # Enviar notificación a través de WebSocket
    await manager.broadcast({
        "event": "user_login",
        "data": {
            "user_id": user.id,
            "username": user.name,
            "roles": roles,
            "device": device_info["device"],
            "os": device_info["os"],
            "browser": device_info["browser"]
        }
    }, exclude=[user.id], roles=[ROLE_ADMIN])
    
    # Enviar un correo de verificación de sesión
    send_email_background(
        request,
        background_tasks,
        subject="Nueva sesión iniciada",
        email_to=user.email,
        template_name="new_session.html",
        body={
            "username": user.name,
            "login_time": settings.CURRENT_TIME.strftime("%Y-%m-%d %H:%M:%S"),
            "year": settings.CURRENT_TIME.year,
            "device": device_info["device"],
            "os": device_info["os"],
            "browser": device_info["browser"],
            "ip": request.client.host,
            "location": {
                "city": device_info.get("city", "Desconocida"),
                "country": device_info.get("country", "Desconocido")
            }
        }
    )

    IS_PROD = settings.ENV == "production"
    response.set_cookie(
        key="csrf_access_token",
        value=access_token,
        httponly=True,
        max_age=int(parse_date(settings.JWT_ACCESS_TOKEN_EXPIRES).total_seconds()),
        secure=IS_PROD,
        samesite="none" if IS_PROD else "lax",
        path="/"
    )
    response.set_cookie(
        key="csrf_refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=int(parse_date(settings.JWT_REFRESH_TOKEN_EXPIRES).total_seconds()),
        secure=IS_PROD,
        samesite="none" if IS_PROD else "lax",
        path="/"
    )
    
    user_data = user.to_dict()
    del user_data["is_connected"]

    return {
        "msg": "Inicio de sesión exitoso",
        "user": user_data
    }


@router.post("/refresh", status_code=status.HTTP_200_OK, tags=["Auth Routes"])  # /api/v1/refresh
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("csrf_refresh_token")
    try:
        payload = verify_token(token)
        user_id = int(payload.get("sub"))

        db_token = db.query(RefreshToken).filter_by(token=token, user_id=user_id, is_active=True).first()
        if not db_token:
            raise HTTPException(status_code=401, detail="Refresh token revocado")

        new_access_token = create_access_token(subject=str(user_id))
        response.set_cookie(
            key="csrf_access_token",
            value=new_access_token,
            httponly=True,
            max_age=int(parse_date(settings.JWT_ACCESS_TOKEN_EXPIRES).total_seconds()),
            secure=True,
            samesite="lax",
            path="/"
        )

        return {"msg": "Token de acceso renovado exitosamente"}
    except jwt.InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Firma del token inválida")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


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


@router.post("/logout", status_code=status.HTTP_200_OK, tags=["Auth Routes"])  # /api/v1/logout
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("csrf_refresh_token")

    try:
        if refresh_token:
            payload = verify_token(refresh_token)
            user_id = int(payload.get("sub"))
            
            # Marcar al usuario como desconectado
            user = db.query(User).filter_by(id=user_id).first()
            if user:
                user.is_connected = False
                db.commit()

            db_token = db.query(RefreshToken).filter_by(token=refresh_token, user_id=user_id).first()
            if db_token:
                db_token.is_active = False
                db.commit()
    except Exception:
        pass  # Token inválido o ya expirado

    response.delete_cookie("csrf_access_token", path="/")
    response.delete_cookie("csrf_refresh_token", path="/")
    return {"msg": "Sesión cerrada exitosamente"}


@router.get("/profile", status_code=status.HTTP_200_OK, tags=["Profile Routes"]) # /api/v1/profile
def profile(
    userInfo: User = Depends(auth_user([ROLE_ALL])),
):
    """Devuelve los datos del perfil del usuario autenticado."""
    return userInfo.to_dict()


@router.put("/profile", status_code=status.HTTP_200_OK, tags=["Profile Routes"]) # /api/v1/profile
async def update_profile(
    data: UpdateProfileSchema,
    userInfo: User = Depends(auth_user([ROLE_ALL])),
    db: Session = Depends(get_db),
    request: Request = None,
    background_tasks: BackgroundTasks = None
):
    """Actualiza los datos del perfil del usuario autenticado."""
    if db.query(User).filter(User.email == data.email, User.id != userInfo.id).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    if data.email != userInfo.email:
        userInfo.is_verified = False
        # Crear el token de verificación
        token = create_secure_token(settings.SECRET_KEY, str(data.email))
        userInfo.token = token
        
        # Enviar correo de verificación
        send_email_background(
            request,
            background_tasks,
            subject="Verificación de nuevo correo",
            email_to=str(data.email),
            template_name="verify_email.html",
            body={
                "username": userInfo.name,
                "verify_url": f"{settings.URL_FRONTEND}/#/?verify-email=true&token={quote(token)}",
                "year": settings.CURRENT_TIME.year
            }
        )
    
    userInfo.name = data.name
    userInfo.email = data.email
    db.commit()
    db.refresh(userInfo)
    
    # Enviar notificación a través de WebSocket
    await manager.broadcast({
        "event": "user_updated",
        "user_id": userInfo.id,
        "user": userInfo.to_dict(),
        "message": "Perfil actualizado"
    }, roles=[ROLE_ADMIN], exclude=[userInfo.id])
    
    return {
        "msg": "Perfil actualizado exitosamente",
        "user": userInfo.to_dict()
    }


@router.put("/profile/update_password", status_code=status.HTTP_200_OK, tags=["Profile Routes"]) # /api/v1/profile/update_password   
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


@router.put("/profile/upload_avatar", status_code=status.HTTP_200_OK, tags=["Profile Routes"])  # /api/v1/profile/upload_avatar
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
                "user_id": user.id,
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
                raise HTTPException(
                    status_code=400,
                    detail="La imagen debe ser cuadrada (mismo ancho y alto)"
                )
            
            if image.width < settings.MINIMUM_IMAGE_DIMENSIONS[0] or image.height < settings.MINIMUM_IMAGE_DIMENSIONS[1]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"La imagen es demasiado pequeña. Dimensiones mínimas: {settings.MINIMUM_IMAGE_DIMENSIONS[0]}x{settings.MINIMUM_IMAGE_DIMENSIONS[1]} píxeles"
                )
                
            if image.width > settings.MAXIMUM_IMAGE_DIMENSIONS[0] or image.height > settings.MAXIMUM_IMAGE_DIMENSIONS[1]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"La imagen es demasiado grande. Dimensiones máximas: {settings.MAXIMUM_IMAGE_DIMENSIONS[0]}x{settings.MAXIMUM_IMAGE_DIMENSIONS[1]} píxeles"
                )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            else:
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
        
        # Enviar notificación a través de WebSocket
        await manager.broadcast({
            "event": "avatar_updated",
            "user_id": user.id,
            "avatar": new_avatar.to_dict(),
            "message": "Avatar actualizado exitosamente"
        }, roles=[ROLE_ADMIN], exclude=[userInfo.id], include=[user.id])

        return {
            "msg": "Avatar subido exitosamente",
            "user_id": user.id,
            "avatar": new_avatar.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir avatar: {str(e)}")
    

@router.delete("/profile/delete_avatar", status_code=status.HTTP_200_OK, tags=["Profile Routes"])  # /api/v1/profile/delete_avatar
async def delete_avatar(
    form_data: AvatarUploadForm = Depends(AvatarUploadForm.as_form),
    userInfo: User = Depends(auth_user([ROLE_ALL])),
    db: Session = Depends(get_db)
):
    """Elimina la imagen de perfil del usuario autenticado."""
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
    
    if not user.avatar_id:
        raise HTTPException(status_code=400, detail="El usuario no tiene un avatar asignado")
    
    user.avatar_id = None
    db.commit()
    db.refresh(user)
    
    # Enviar notificación a través de WebSocket
    await manager.broadcast({
        "event": "avatar_deleted",
        "user_id": user.id,
        "message": "Avatar eliminado exitosamente"
    }, roles=[ROLE_ADMIN], exclude=[userInfo.id], include=[user.id])

    return {"msg": "Avatar eliminado exitosamente", "user_id": user.id}
