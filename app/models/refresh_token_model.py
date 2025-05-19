from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship, validates
from dotenv import load_dotenv
from datetime import datetime, timezone
import json

from app.config.database import Base
from app.config.settings import settings
from app.utils.parse import parse_date 

load_dotenv()

refresh_expires_in = parse_date(settings.JWT_REFRESH_TOKEN_EXPIRES)
access_expires_in = parse_date(settings.JWT_ACCESS_TOKEN_EXPIRES)

class RefreshToken(Base):
    """Modelo de tokens de actualización."""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(500), nullable=False, unique=True)
    created_at = Column(DateTime, default=settings.CURRENT_TIME, nullable=False)
    expires_at = Column(DateTime, nullable=False)  # Nueva columna para expiración
    device_info = Column(JSON, nullable=False)  # Información del dispositivo
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="refresh_tokens")

    def __init__(self, user_id, token, device_info, expires_in=refresh_expires_in):
        """ 
        expires_in: número de días antes de que el token expire (por defecto 30 días)
        """
        self.user_id = user_id
        self.token = token
        self.expires_at = settings.CURRENT_TIME + expires_in
        self.device_info = json.loads(json.dumps(device_info)) # Crear esta columna en la base de datos
    
    def __str__(self):
        return f"RefreshToken(id={self.id}, user_id={self.user_id}, token={self.token}, expires_at={self.expires_at}, is_active={self.is_active})"
    
    def __eq__(self, other):
        if not isinstance(other, RefreshToken):
            return False
        return self.id == other.id and self.user_id == other.user_id and self.token == other.token
        
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "token": self.token,
            "expires_at": self.expires_at,
            "is_active": self.is_active
        }
        
    def __repr__(self):
        return f"<RefreshToken {self.id}>"
    
    # Método para verificar si el token ha expirado
    def is_expired(self):
        return datetime.now(timezone.utc) > self.expires_at
    
    # Método para invalidar el token
    def invalidate(self):
        self.is_active = False
        self.expires_at = datetime.now(timezone.utc)  # Establecer la fecha de expiración a ahora
