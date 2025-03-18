from config.database import db
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from datetime import datetime, timedelta

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
        self.expires_at = datetime.utcnow() + timedelta(days=expires_in)
