import os
import re
from pydantic import BaseSettings
from datetime import timedelta
from dotenv import load_dotenv

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

BASE_DIR = os.path.expanduser("~")  # Directorio base (donde se crearan y guardaran los archivos)

APP_DIR = os.path.join(BASE_DIR, 'DocTools')  # Directorio de la aplicación

DATABASE_USER = os.getenv("DB_USER")
DATABASE_PASSWORD = os.getenv("DB_PASSWORD")
DATABASE_HOST = os.getenv("DB_HOST")
DATABASE_NAME = os.getenv("DB_NAME")
DATABASE_PORT = os.getenv("DB_PORT", 3306)

JWT_ACCESS_TOKEN_EXPIRES_IN = parse_date(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_IN")) # 1d
JWT_REFRESH_TOKEN_EXPIRES_IN = parse_date(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_IN")) # 3d

class Settings(BaseSettings):
    """Configuración de la aplicación."""
    UPLOAD_FOLDER: str = os.path.join(APP_DIR, 'files')
    QR_FOLDER: str = os.path.join(APP_DIR, 'qrs')
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")   # Clave secreta para JWT
    ALLOWED_EXTENSIONS: set = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16 MB
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = JWT_ACCESS_TOKEN_EXPIRES_IN
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = JWT_REFRESH_TOKEN_EXPIRES_IN
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    DEBUG: bool = True
    PORT: int = 5000
    HOST: str = "127.0.0.1"
    BASE_DIR: str = BASE_DIR
    APP_DIR: str = APP_DIR
    STATIC_FOLDER: str = os.path.join(APP_DIR, 'static')
    
    # Configuración de la base de datos
    DATABASE_URI : str = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
settings_dict = settings.dict()