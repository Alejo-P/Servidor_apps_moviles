import os
from typing import ClassVar
from pydantic import BaseSettings
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

class Settings(BaseSettings):
    """Configuración de la aplicación."""
    BASE_URL: ClassVar[str] = os.getenv("BASE_URL", "http://localhost:5000")
    API_V1_STR: str = "/api/v1"  # Prefijo de la API
    
    BASE_DIR: str = os.path.expanduser("~") # Directorio base (donde se crearan y guardaran los archivos)
    APP_DIR: str = os.path.join(BASE_DIR, 'DocTools')  # Directorio de la aplicación
    UPLOAD_FOLDER: str = os.path.join(APP_DIR, 'files')
    QR_FOLDER: str = os.path.join(APP_DIR, 'qrs')
    STATIC_FOLDER: str = os.path.join(APP_DIR, 'static')
    LOG_FOLDER: str = os.path.join(APP_DIR, 'logs')
    LOG_FILE: str = os.path.join(LOG_FOLDER, 'app.log')
    
    PYTHONUNBUFFERED: int = 1  # Evita el buffering de salida
    ALLOWED_EXTENSIONS: set = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16 MB
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    
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
    
    # Configuración de la base de datos
    DB_URI: str = os.getenv("DB_URI", "mysql+pymysql://user:password@localhost/dbname")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()