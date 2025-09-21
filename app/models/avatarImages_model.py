from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base
from app.config.settings import settings

class AvatarImage(Base):
    __tablename__ = "avatar_images"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    url = Column(String(255), nullable=False)
    public_id = Column(String(255), nullable=False, unique=True)
    hash_id = Column(String(255), nullable=False, unique=True)
    format = Column(String(255), nullable=False)
    width = Column(Integer)
    height = Column(Integer)
    created_at = Column(DateTime, default=settings.CURRENT_TIME, nullable=False)

    users = relationship("User", back_populates="avatar")
    
    def __init__(self, url, name, public_id, hash_id, format, width=None, height=None):
        self.url = url
        self.name = name
        self.public_id = public_id
        self.hash_id = hash_id
        self.format = format
        self.width = width
        self.height = height

    def __repr__(self):
        return f"<AvatarImage {self.public_id}>"
    
    def to_dict(self):
        """Devuelve un diccionario con los datos de la imagen del avatar."""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "public_id": self.public_id,
            "format": self.format,
            "width": self.width,
            "height": self.height,
            "used_by": [{"user_id": user.id, "name": user.name} for user in self.users],
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }