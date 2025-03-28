import os
from config.database import db
from config.settings import JWT_REFRESH_TOKEN_EXPIRES_IN, JWT_ACCESS_TOKEN_EXPIRES_IN
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# Mostrar las variables de entorno
print("Variables de entorno:")
print("Access token expires in:", JWT_ACCESS_TOKEN_EXPIRES_IN)
print("Refresh token expires in:", JWT_REFRESH_TOKEN_EXPIRES_IN)

refresh_expires_in = JWT_REFRESH_TOKEN_EXPIRES_IN
access_expires_in = JWT_ACCESS_TOKEN_EXPIRES_IN

class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(500), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)  # Nueva columna para expiración
    is_active = Column(Boolean, default=True)

    def __init__(self, user_id, token, expires_in=30):
        """ 
        expires_in: número de días antes de que el token expire (por defecto 30 días)
        """
        self.user_id = user_id
        self.token = token
        self.expires_at = datetime.now(timezone.utc) + refresh_expires_in
        
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
