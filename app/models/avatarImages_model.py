from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base

class AvatarImage(Base):
    __tablename__ = "avatar_images"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    public_id = Column(String, nullable=False, unique=True)
    hash_id = Column(String, nullable=False, unique=True)
    format = Column(String, nullable=False)
    width = Column(Integer)
    height = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="avatar")
    
    def __init__(self, url, public_id, hash_id, format, width=None, height=None):
        self.url = url
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
            "url": self.url,
            "public_id": self.public_id,
            "format": self.format,
            "width": self.width,
            "height": self.height,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }