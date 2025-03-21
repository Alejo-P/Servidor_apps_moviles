from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from config.database import db

class QRCode(db.Model):
    """Modelo de códigos QR."""
    __tablename__ = "qrcodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    text = Column(String(500), nullable=False)
    filename = Column(String(255), nullable=False)  # Ruta del archivo QR
    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    def __init__(self, name, text, filename, created_by):
        self.name = name
        self.text = text
        self.filename = filename
        self.created_by = created_by
        
    def __repr__(self):
        return f"<QRCode {self.name}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "text": self.text,
            "filename": self.filename
        }