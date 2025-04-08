from config.database import db
from sqlalchemy import Column, Integer, String, DateTime    
from datetime import datetime

class Role(db.Model):
    """Modelo de roles."""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
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
            "created_at": self.created_at
        }   