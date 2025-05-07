from app.config.database import Base
from app.config.settings import settings
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import validates

class File(Base):
    """Modelo de archivos."""
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(100), unique=True, nullable=False)
    filepath = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    uploaded_at = Column(DateTime, default=settings.CURRENT_TIME, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    qr_code = Column(Integer, ForeignKey("qrcodes.id"), nullable=True)
    
    def __init__(self, filename, filepath, file_size, file_type, uploaded_by):
        self.filename = filename
        self.filepath = filepath
        self.file_size = file_size
        self.file_type = file_type
        self.uploaded_by = uploaded_by
        
    def __repr__(self):
        return f"<File {self.filename}>"
    
    def to_dict(self):
        """Devuelve un diccionario con los datos del archivo."""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "uploaded_at": self.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
            "uploaded_by": self.uploaded_by,
            "qr_code": self.qr_code
        }
    
    @validates("filename")
    def validate_filename(self, key, filename):
        """Valida el nombre del archivo."""
        if not filename:
            raise ValueError("El nombre del archivo es requerido.")
        
        return filename
    
    @validates("filepath")
    def validate_filepath(self, key, filepath):
        """Valida la ruta del archivo."""
        if not filepath:
            raise ValueError("La ruta del archivo es requerida.")
        
        return filepath
    
    @validates("file_size")
    def validate_file_size(self, key, file_size):
        """Valida el tamaño del archivo."""
        if file_size is None or file_size < 0:
            raise ValueError("El tamaño del archivo no puede ser negativo ni nulo.")
        return file_size
    
    @validates("file_type")
    def validate_file_type(self, key, file_type):
        """Valida el tipo de archivo."""
        if not file_type:
            raise ValueError("El tipo de archivo es requerido.")
        
        return file_type
    