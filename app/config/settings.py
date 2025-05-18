import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import ClassVar
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

class Settings(BaseSettings):
    """Configuración de la aplicación."""

    @property
    def LOGS_DIR(self) -> str:
        tz = ZoneInfo(self.TIMEZONE)
        # Crear el directorio de logs si no existe
        os.makedirs(os.path.join(self.SERVER_DIR, 'logs'), exist_ok=True)
        os.makedirs(os.path.join(self.SERVER_DIR, 'logs', str(datetime.now(tz).year)), exist_ok=True)
        now = datetime.now(tz)
        return os.path.join(self.SERVER_DIR, 'logs', str(now.year), f"{now.month:02}", f"{now.day:02}")
    
    @property
    def CURRENT_TIME(self) -> datetime:
        tz = ZoneInfo(self.TIMEZONE)
        now = datetime.now(tz)
        return now
    
    BASE_URL: ClassVar[str] = os.getenv("BASE_URL", "http://localhost:5000")
    API_V1_STR: str = "/api/v1"  # Prefijo de la API
    URL_FRONTEND: str = os.getenv("URL_FRONTEND", "http://localhost:5173")  # URL del frontend
    URL_BACKEND: str = os.getenv("URL_BACKEND", "http://localhost:5000")  # URL del backend
    ENV: str = os.getenv("ENV", "development")  # Entorno de la aplicación (development, production, etc.)
    
    BASE_DIR: str = os.path.expanduser("~") # Directorio base (donde se crearan y guardaran los archivos)
    SERVER_DIR: Path = Path(__file__).resolve().parent.parent  # Directorio del servidor
    APP_DIR: str = os.path.join(BASE_DIR, 'DocTools')  # Directorio de la aplicación
    UPLOAD_FOLDER: str = os.path.join(APP_DIR, 'files')
    QR_FOLDER: str = os.path.join(APP_DIR, 'qrs')
    STATIC_FOLDER: str = os.path.join(APP_DIR, 'static')
    TEMPLATES_FOLDER: str = os.path.join(SERVER_DIR, "templates")
    EMAIL_TEMPLATES_FOLDER: str = os.path.join(TEMPLATES_FOLDER, "email")
    
    PYTHONUNBUFFERED: int = 1  # Evita el buffering de salida
    ALLOWED_EXTENSIONS: set = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16 MB
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default_secret_key")  # Clave secreta para la aplicación
    
    AUTHJWT_SECRET_KEY: str = os.getenv("AUTHJWT_SECRET_KEY")   # Clave secreta para JWT
    JWT_ACCESS_CSRF_COOKIE: bool = os.getenv("JWT_ACCESS_CSRF_COOKIE", "True") == "True"
    JWT_REFRESH_CSRF_COOKIE: bool = os.getenv("JWT_REFRESH_CSRF_COOKIE", "True") == "True"
    AUTH_COOKIE_SECURE: bool = os.getenv("AUTH_COOKIE_SECURE", "False") == "True"  # Solo para HTTPS
    JWT_ACCESS_TOKEN_EXPIRES: str = os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "1d")
    JWT_REFRESH_TOKEN_EXPIRES: str = os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "3d")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    
    DEBUG: bool = True
    PORT: int = 5000
    HOST: str = "127.0.0.1"
    MAX_FILE_SIZE_MB: int = 2
    ALLOWED_MIME_TYPES: list = ["image/jpeg", "image/png", "image/webp"]
    TIMEZONE: str = os.getenv("TIMEZONE", "UTC")  # Zona horaria por defecto
    
    # Configuración de Cloudinary
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")
    CLOUDINARY_URL: str = os.getenv("CLOUDINARY_URL", "")
    
    # Configuración de la base de datos
    DB_URI: str = os.getenv("DB_URI", "mysql+pymysql://user:password@localhost/dbname")
    
    # Configuración para el logger
    LOG_MAX_BYTES: int = 1024 * 1024 * 5  # 5 MB
    LOG_BACKUP_COUNT: int = 5  # Número de archivos de respaldo
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")  # Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_BY_HOUR: bool = True # Si se desea log por hora
    
    # Configuracion de FastMail
    MAIL_USERNAME: str = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD: str = os.getenv('MAIL_PASSWORD')
    MAIL_FROM: str = os.getenv('MAIL_FROM')
    MAIL_PORT: int = int(os.getenv('MAIL_PORT'))
    MAIL_SERVER: str = os.getenv('MAIL_SERVER')
    MAIL_FROM_NAME: str = os.getenv('MAIL_FROM_NAME')
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Permitir variables no definidas en el modelo

settings = Settings()