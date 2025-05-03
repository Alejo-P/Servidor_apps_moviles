from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_jwt_auth.exceptions import MissingTokenError, JWTDecodeError
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.roles_model import Role
from app.models.users_model import User
from app.middlewares.auth import auth_user
from app.config.constants import *
from app.schemas.role_user_schema import RoleUserSchema

router = APIRouter()

@router.get("/users", status_code=status.HTTP_200_OK) # /api/v1/users
def get_all_profiles(
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Devuelve todos los perfiles de usuario."""
    try:
        users = db.query(User).all()
        return [user.to_dict() for user in users]
    except (JWTDecodeError, MissingTokenError) as e:
        raise HTTPException(status_code=401, detail="Token inválido o faltante")


@router.get("/user/{user_id}", status_code=status.HTTP_200_OK) # /api/v1/user/<user_id>
def get_user_profile(
    user_id: int,
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Devuelve los datos del perfil de un usuario específico."""
    try:
        user = db.query(User).get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return user.to_dict()
    except (JWTDecodeError, MissingTokenError) as e:
        raise HTTPException(status_code=401, detail="Token inválido o faltante")


@router.post("/user/activate/{user_id}", status_code=status.HTTP_200_OK) # /api/v1/user/activate/<user_id>
def activate_user_profile(
    user_id: int,
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Activar el perfil del usuario."""
    user_roles = [role.name for role in userInfo.roles]
    if ROLE_ADMIN in user_roles:
        user = db.get(User, user_id)
    else:
        user = db.get(User, userInfo.id)
        if userInfo.id != user_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para activar el perfil de otro usuario")
        
    user.is_active = True
    db.commit()
    db.refresh(user)
             
    return {"msg": "Perfil activado exitosamente"}


@router.post("/user/deactivate/{user_id}", status_code=status.HTTP_200_OK) # /api/v1/user/deactivate/<user_id>
def delete_user(
    user_id: int,
    user_info: dict = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Desactivar el perfil del usuario."""
    user_roles = user_info.get("roles", [])
    if ROLE_ADMIN in user_roles:
        user = db.get(User, user_id)
    else:
        user = db.get(User, user_info.get("id"))
        if user.id != user_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para eliminar el perfil de otro usuario")
        
    user.is_active = False
    db.commit()
    db.refresh(user)
             
    return {"msg": "Perfil desactivado exitosamente"}


@router.put("/user/{user_id}", status_code=status.HTTP_200_OK) # /api/v1/user/<user_id>
def update_user_profile(
    user_id: int,
    user_info: dict = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Actualizar el perfil del usuario."""
    user_roles = user_info.get("roles", [])
    if ROLE_ADMIN in user_roles:
        user = db.get(User, user_id)
    else:
        user = db.get(User, user_info.get("id"))
        if user.id != user_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para actualizar el perfil de otro usuario")
        
    # Aquí puedes agregar la lógica para actualizar los datos del usuario
    # Por ejemplo, si estás usando un esquema Pydantic para validar los datos de entrada
    
    db.commit()
    db.refresh(user)
    
    return {"msg": "Perfil actualizado exitosamente"}

 
@router.post("/add_role", status_code=status.HTTP_200_OK) # /api/v1/add_role
def add_role_to_user(
    data: RoleUserSchema,
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
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
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
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