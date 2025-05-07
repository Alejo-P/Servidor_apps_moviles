from app.config.database import Base
from app.config.settings import settings
from sqlalchemy import Column, Integer, String, DateTime

class Role(Base):
    """Modelo de roles."""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=settings.CURRENT_TIME, nullable=False)
    
    def __init__(self, name, description=None):
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
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }   