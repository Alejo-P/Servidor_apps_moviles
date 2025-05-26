from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from urllib.parse import quote

from app.config.database import get_db
from app.config.mailer import send_email_background
from app.models.roles_model import Role
from app.models.users_model import User
from app.models.userAction_model import ActionType, UserAction
from app.middlewares.auth import auth_user
from app.config.constants import *
from app.schemas.modify_user_schema import ModifyUserSchema
from app.schemas.role_user_schema import RoleUserSchema
from app.schemas.role_register_schema import RoleRegisterSchema
from app.schemas.update_profile_schema import UpdateProfileSchema, UpdatePasswordSchema
from app.utils.verif_token import verify_secure_token, create_secure_token
from app.config.settings import settings
from app.sockets.websockets import manager

router = APIRouter()

@router.get("/users", status_code=status.HTTP_200_OK, tags=["Admin Routes"]) # /api/v1/users
def get_all_profiles(
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Devuelve todos los perfiles de usuario."""
    users = db.query(User).all()
    users_dicts = [user.to_dict() for user in users]

    # Separar al usuario autenticado
    auth_user_dict = next((u for u in users_dicts if u["id"] == userInfo.id), None)
    other_users = [u for u in users_dicts if u["id"] != userInfo.id]

    return [auth_user_dict] + other_users if auth_user_dict else users_dicts


@router.get("/user/{user_id}", status_code=status.HTTP_200_OK, tags=["Admin Routes"]) # /api/v1/user/<user_id>
def get_user_profile(
    user_id: int,
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Devuelve los datos del perfil de un usuario específico."""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return user.to_dict()


@router.post("/user/activate", status_code=status.HTTP_200_OK, tags=["Admin Routes"]) # /api/v1/user/activate
async def activate_user_profile(
    data: ModifyUserSchema,
    background_tasks: BackgroundTasks,
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Activar el perfil del usuario."""
    user_roles = [role.name for role in userInfo.roles]
    if ROLE_ADMIN in user_roles:
        user = db.get(User, data.user_id)
    else:
        user = db.get(User, userInfo.id)
        if userInfo.id != data.user_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para activar el perfil de otro usuario")
         
    # Verificar si el usuario existe
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar si el usuario ya está activo
    if user.is_active:
        raise HTTPException(status_code=400, detail="El perfil ya está activo")
        
    user.is_active = True
    db.commit()
    db.refresh(user)
    
    accion = UserAction(
        user_id=user.id,
        action=ActionType.activado,
        reason=data.reason
    )
    db.add(accion)
    db.commit()
    db.refresh(accion)
    
    # Enviar un correo de notificacion al usuario
    send_email_background(
        background_tasks,
        subject="Activacion de cuenta",
        email_to=user.email,
        template_name="activate_account.html",
        body={
            "username": user.name,
            "login_url": f"{settings.URL_FRONTEND}/#/?login=true",
            "year": settings.CURRENT_TIME.year
        }
    )
    
    # Enviar notificación a través de WebSocket
    if user:
        await manager.broadcast({
            "event": "user_activated",
            "user_id": user.id,
            "message": "Tu cuenta ha sido activada exitosamente"
        }, roles=[ROLE_ADMIN], exclude=[userInfo.id])
             
    return {"msg": "Perfil activado exitosamente"}


@router.post("/user/deactivate", status_code=status.HTTP_200_OK, tags=["Admin Routes"]) # /api/v1/user/deactivate
async def deactivate_user_profile(
    data: ModifyUserSchema,
    background_tasks: BackgroundTasks,
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Desactivar el perfil del usuario."""
    user_roles = [role.name for role in userInfo.roles]
    if ROLE_ADMIN in user_roles:
        user = db.get(User, data.user_id)
    else:
        user = db.get(User, userInfo.id)
        if user.id != data.user_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para eliminar el perfil de otro usuario")
        
    # Verificar si el usuario existe
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar si el usuario ya está desactivado
    if not user.is_active:
        raise HTTPException(status_code=400, detail="El perfil ya está desactivado")
        
    user.is_active = False
    user.token = None
    db.commit()
    db.refresh(user)
    
    accion = UserAction(
        user_id=user.id,
        action=ActionType.desactivado,
        reason=data.reason
    )
    db.add(accion)
    db.commit()
    db.refresh(accion)
    
    # Enviar un correo de notificacion al usuario
    send_email_background(
        background_tasks,
        subject="Desactivacion de cuenta",
        email_to=user.email,
        template_name="deactivate_account.html",
        body={
            "username": user.name,
            "support_email": userInfo.email,
            "support_url": f"{settings.URL_FRONTEND}/#/?support=true",
            "year": settings.CURRENT_TIME.year
        }
    )
    
    # Enviar notificación a través de WebSocket
    if user:
        await manager.broadcast({
            "event": "user_deactivated",
            "user_id": user.id,
            "message": "Tu cuenta ha sido desactivada"
        }, roles=[ROLE_ADMIN], exclude=[userInfo.id], include=[user.id])
             
    return {"msg": "Perfil desactivado exitosamente"}


@router.put("/user/{user_id}", status_code=status.HTTP_200_OK, tags=["Admin Routes"]) # /api/v1/user/<user_id>
async def update_user_profile(
    user_id: int,
    data: UpdateProfileSchema,
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Actualizar el perfil del usuario."""
    user_roles = [role.name for role in userInfo.roles]
    if ROLE_ADMIN in user_roles:
        user = db.get(User, user_id)
    else:
        user = db.get(User, userInfo.id)
        if user.id != user_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para actualizar el perfil de otro usuario")
        
    # Verificar si el correo ya está en uso por otro usuario
    existing_user = db.query(User).filter(User.email == data.email, User.id != user.id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El correo ya está en uso por otro usuario")
    
    # Actualizar los datos del usuario    
    user.name = data.name
    user.email = data.email
    db.commit()
    db.refresh(user)
    
    # Enviar notificación a través de WebSocket
    if user:
        await manager.broadcast({
            "event": "user_updated",
            "user_id": user.id,
            "user": user.to_dict(),
            "message": "El perfil ha sido actualizado exitosamente"
        }, roles=[ROLE_ADMIN], exclude=[userInfo.id], include=[user.id])
    
    return {
        "msg": "Usuario actualizado exitosamente",
        "user": user.to_dict()
    }
    

@router.put("/user/change-password/{user_id}", status_code=status.HTTP_200_OK, tags=["Admin Routes"]) # /api/v1/user/change-password/<user_id>
def update_user_password(
    user_id: int,
    data: UpdatePasswordSchema,
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Actualizar la contraseña del usuario."""
    user_roles = [role.name for role in userInfo.roles]
    if ROLE_ADMIN in user_roles:
        user = db.get(User, user_id)
    else:
        user = db.get(User, userInfo.id)
        if user.id != user_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para cambiar la contraseña de otro usuario")
        
    # Verificar si la contraseña actual es correcta
    if not user.check_password(data.current_password):
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")
    
    # Verificar si la nueva contraseña es igual a la actual
    if data.new_password == data.current_password:
        raise HTTPException(status_code=400, detail="La nueva contraseña no puede ser igual a la actual")
    
    # Verificar que la nueva contraseña cumpla con los requisitos
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe tener al menos 8 caracteres")
    
    if not any(char.isdigit() for char in data.new_password):
        raise HTTPException(status_code=400, detail="La nueva contraseña debe contener al menos un número")
    
    # Verificar si las contraseñas coinciden
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")
    
    # Actualizar la contraseña
    user.password = data.new_password
    db.commit()
    db.refresh(user)
    
    return {"msg": "Contraseña actualizada exitosamente"}


@router.post("/create_role", status_code=status.HTTP_201_CREATED, tags=["Role Routes"]) # /api/v1/create_role
def create_role(
    data: RoleRegisterSchema,
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Crea un nuevo rol."""
    role = Role(
        name=data.role_name,
        permissions=data.permissions,
        description=data.description
    )
    
    db.add(role)
    db.commit()
    db.refresh(role)
    
    return {"msg": "Rol creado exitosamente", "role": role.to_dict()}
    
    
@router.get("/roles", status_code=status.HTTP_200_OK, tags=["Role Routes"]) # /api/v1/roles
def get_all_roles(
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Devuelve todos los roles."""
    roles = db.query(Role).all()
    roles_dicts = [{"id": role.id, "name":role.name} for role in roles]
    
    return roles_dicts
    
    
@router.get("/role/{role_id}", status_code=status.HTTP_200_OK, tags=["Role Routes"]) # /api/v1/role/<role_id>
def get_role(
    role_id: str,
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Devuelve los datos de un rol específico."""
    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    return role.to_dict()
    

@router.put("/role/{role_id}", status_code=status.HTTP_200_OK, tags=["Role Routes"]) # /api/v1/role/<role_id>
def update_role(
    role_id: int,
    data: RoleRegisterSchema,
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Actualizar un rol."""
    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    role.name = data.role_name
    role.permissions = data.permissions
    if data.description:
        role.description = data.description
    role.updated_at = settings.CURRENT_TIME
    
    db.commit()
    db.refresh(role)
    
    return {"msg": "Rol actualizado exitosamente", "role": role.to_dict()}


@router.delete("/role/{role_id}", status_code=status.HTTP_200_OK, tags=["Role Routes"]) # /api/v1/role/<role_id>
def delete_role(
    role_id: int,
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Eliminar un rol."""
    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    # Verificar si el rol está asignado a algún usuario
    if role.users:
        raise HTTPException(status_code=400, detail="No se puede eliminar un rol asignado a usuarios")

    db.delete(role)
    db.commit()

    return {"msg": "Rol eliminado exitosamente"}

 
@router.post("/add_role", status_code=status.HTTP_200_OK, tags=["Role Routes"]) # /api/v1/add_role
async def add_role_to_user(
    data: RoleUserSchema,
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Agrega un rol a un usuario."""
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
    
    # Enviar notificación a través de WebSocket
    if user:
        await manager.broadcast({
            "event": "role_added",
            "user_id": user.id,
            "role_name": role.name,
            "message": f"Se te ha asignado el rol de {role.name}"
        }, roles=[ROLE_ADMIN], exclude=[userInfo.id], include=[user.id])
    
    return {"msg": "Rol agregado exitosamente"}
    
    
@router.delete("/remove_role", status_code=status.HTTP_200_OK, tags=["Role Routes"]) # /api/v1/remove_role
async def remove_role_from_user(
    data: RoleUserSchema,
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Elimina un rol de un usuario."""
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
    
    # Enviar notificación a través de WebSocket
    if user:
        await manager.broadcast({
            "event": "role_removed",
            "user_id": user.id,
            "role_name": role.name,
            "message": f"Se te ha removido el rol de {role.name}"
        }, roles=[ROLE_ADMIN], exclude=[userInfo.id], include=[user.id])
    
    return {"msg": "Rol eliminado exitosamente"}


@router.post("/send-verification-email/{user_id}", status_code=status.HTTP_200_OK, tags=["Admin Routes"]) # /api/v1/send-verification-email/<user_id>
def send_verification_email(
    user_id: int,
    background_tasks: BackgroundTasks,
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Enviar un correo de verificación al usuario."""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    token = user.token
    if not token or not verify_secure_token(settings.SECRET_KEY, token):
        # Si el token no es válido o no existe, crear uno nuevo
        token = create_secure_token(settings.SECRET_KEY, user.email)
        user.token = token
        db.commit()
        db.refresh(user)
    
    # Verificar si el correo ya ha sido verificado
    if user.is_verified and user.is_active:
        raise HTTPException(status_code=400, detail="El correo ya ha sido verificado")
    
    # Envio del correo de verificación
    send_email_background(
        background_tasks,
        subject="Verificación de cuenta",
        email_to=user.email,
        template_name="verify_email.html",
        body={
            "username": user.name,
            "verify_url": f"{settings.URL_FRONTEND}/#/?verify-email=true&token={quote(token)}",
            "year": settings.CURRENT_TIME.year
        }
    )
    
    return {"msg": "Correo de verificación enviado exitosamente"}