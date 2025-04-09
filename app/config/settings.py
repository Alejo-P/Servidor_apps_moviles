import os
import re
from typing import ClassVar
from pydantic import BaseSettings
from datetime import timedelta
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

def parse_date(value: str):
    """Parses a duration string (e.g., '3d', '6h30m', '2d4h20m10s') into a timedelta object."""
    if not value:
        return timedelta(days=1)  # Valor por defecto: 1 día

    # Expresión regular para capturar números seguidos de unidades (d, h, m, s)
    pattern = re.findall(r"(\d+)([dhms])", value)
    
    if not pattern:
        raise ValueError(f"Formato inválido: '{value}'. Usa formatos como '1d', '3h30m', '45m10s'.")

    # Mapeo de unidades a timedelta
    tiempo_total = timedelta()
    unidades = {"d": "days", "h": "hours", "m": "minutes", "s": "seconds"}

    for cantidad, unidad in pattern:
        cantidad = int(cantidad)
        tiempo_total += timedelta(**{unidades[unidad]: cantidad})

    return tiempo_total

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
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")   # Clave secreta para JWT
    ALLOWED_EXTENSIONS: set = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16 MB
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    JWT_ACCESS_TOKEN_EXPIRES: str = int(parse_date(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "1d")).total_seconds())
    JWT_REFRESH_TOKEN_EXPIRES: str = int(parse_date(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "3d")).total_seconds())
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