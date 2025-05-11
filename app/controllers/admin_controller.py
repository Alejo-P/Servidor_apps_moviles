from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.roles_model import Role
from app.models.users_model import User
from app.middlewares.auth import auth_user
from app.config.constants import *
from app.schemas.role_user_schema import RoleUserSchema
from app.schemas.role_register_schema import RoleRegisterSchema
from app.models.userRoles_model import user_roles
from app.config.settings import settings

router = APIRouter()

@router.get("/users", status_code=status.HTTP_200_OK) # /api/v1/users
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


@router.get("/user/{user_id}", status_code=status.HTTP_200_OK) # /api/v1/user/<user_id>
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
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Desactivar el perfil del usuario."""
    user_roles = [role.name for role in userInfo.roles]
    if ROLE_ADMIN in user_roles:
        user = db.get(User, user_id)
    else:
        user = db.get(User, userInfo.id)
        if user.id != user_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para eliminar el perfil de otro usuario")
        
    user.is_active = False
    db.commit()
    db.refresh(user)
             
    return {"msg": "Perfil desactivado exitosamente"}


@router.put("/user/{user_id}", status_code=status.HTTP_200_OK) # /api/v1/user/<user_id>
def update_user_profile(
    user_id: int,
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
        
    # Aquí puedes agregar la lógica para actualizar los datos del usuario
    # Por ejemplo, si estás usando un esquema Pydantic para validar los datos de entrada
    
    db.commit()
    db.refresh(user)
    
    return {"msg": "Perfil actualizado exitosamente"}


@router.post("/create_role", status_code=status.HTTP_201_CREATED) # /api/v1/create_role
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
    
    
@router.get("/roles", status_code=status.HTTP_200_OK) # /api/v1/roles
def get_all_roles(
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Devuelve todos los roles."""
    roles = db.query(Role).all()
    roles_dicts = [role.to_dict() for role in roles]
    
    return roles_dicts
    
    
@router.get("/role/{role_id}", status_code=status.HTTP_200_OK) # /api/v1/role/<role_id>
def get_role(
    role_id: int,
    userInfo: User = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """Devuelve los datos de un rol específico."""
    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    return role.to_dict()
    

@router.put("/role/{role_id}", status_code=status.HTTP_200_OK) # /api/v1/role/<role_id>
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


@router.delete("/role/{role_id}", status_code=status.HTTP_200_OK) # /api/v1/role/<role_id>
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

 
@router.post("/add_role", status_code=status.HTTP_200_OK) # /api/v1/add_role
def add_role_to_user(
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
    
    return {"msg": "Rol agregado exitosamente"}
    
    
@router.delete("/remove_role", status_code=status.HTTP_200_OK) # /api/v1/remove_role
def remove_role_from_user(
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
    
    return {"msg": "Rol eliminado exitosamente"}