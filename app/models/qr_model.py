from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.config.database import Base

class QRCode(Base):
    """Modelo de códigos QR."""
    __tablename__ = "qrcodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    text = Column(String(500), nullable=False)
    filepath = Column(String(255), nullable=False)  # Ruta del archivo QR
    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    def __init__(self, filename, text, filepath, created_by):
        self.filename = filename
        self.text = text
        self.filepath = filepath
        self.created_by = created_by
        
    def __repr__(self):
        return f"<QRCode {self.filename}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "text": self.text,
            "filepath": self.filepath,
            "created_at": self.created_at,
            "created_by": self.created_by
        }