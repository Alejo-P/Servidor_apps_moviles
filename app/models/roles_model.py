from app.config.database import Base
from app.config.settings import settings
from app.config.constants import PERMISSIONS
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import validates

class Role(Base):
    """Modelo de roles."""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=settings.CURRENT_TIME, nullable=False)
    updated_at = Column(DateTime, default=settings.CURRENT_TIME, nullable=False)
    
    def __init__(self, name, description=None):
        """Inicializa el rol."""
        self.name = name
        self.description = description
        
    def __repr__(self):
        return f"<Role {self.name}>"
    
    def to_dict(self):
        """Devuelve un diccionario con los datos del rol."""
        return {
            "id": self.id,
            "name": self.name,
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
    
    @validates("description")
    def validate_description(self, key, description):
        """Valida la descripción del rol."""
        if description and len(description) > 255:
            raise ValueError("La descripción no puede exceder los 255 caracteres.")
        
        return description