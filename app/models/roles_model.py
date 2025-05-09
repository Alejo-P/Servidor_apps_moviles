from app.config.database import Base
from app.config.settings import settings
from app.config.constants import PERMISSIONS
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import validates, relationship

class Role(Base):
    """Modelo de roles."""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    permissions = Column(JSON, nullable=False)  # Lista de permisos en formato JSON o similar
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=settings.CURRENT_TIME, nullable=False)
    updated_at = Column(DateTime, default=settings.CURRENT_TIME, nullable=False)
    
    def __init__(self, name, description=None, permissions=None):
        """Inicializa el rol."""
        self.name = name
        self.description = description
        self.permissions = permissions if permissions is not None else []
        
    def __repr__(self):
        return f"<Role {self.name}>"
    
    def to_dict(self):
        """Devuelve un diccionario con los datos del rol."""
        return {
            "id": self.id,
            "name": self.name,
            "permissions": self.permissions,
            "description": self.description,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        
    @validates("name")
    def validate_name(self, key, name):
        """Valida el nombre del rol."""
        if not name:
            raise ValueError("El nombre del rol es requerido.")
        
        return name
    
    @validates("permissions")
    def validate_permissions(self, key, permissions):
        """Valida los permisos del rol."""
        if not isinstance(permissions, list):
            raise ValueError("Los permisos deben ser una lista.")
        
        if not all(isinstance(permission, str) for permission in permissions):
            raise ValueError("Todos los permisos deben ser cadenas de texto.")

        # Construir set de permisos válidos: {file:upload, qr:create_from_text, ...}
        allowed_permissions = {
            f"{resource}:{action}" for resource, actions in PERMISSIONS.items() for action in actions
        }

        invalid_permissions = [p for p in permissions if p not in allowed_permissions]
        if invalid_permissions:
            raise ValueError(f"Permisos no válidos: {', '.join(invalid_permissions)}")

        return permissions
    
    @validates("description")
    def validate_description(self, key, description):
        """Valida la descripción del rol."""
        if description and len(description) > 255:
            raise ValueError("La descripción no puede exceder los 255 caracteres.")
        
        return description