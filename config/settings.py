import os
import re
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

# Configuración del servidor (para producción)
DEBUG = True
PORT = 5000
HOST = "0.0.0.0"

BASE_DIR = os.path.expanduser("~")  # Directorio base (donde se crearan y guardaran los archivos)

APP_DIR = os.path.join(BASE_DIR, 'DocTools')  # Directorio de la aplicación

# Configuración de archivos
UPLOAD_FOLDER = os.path.join(APP_DIR, 'uploads')  # Carpeta de archivos subidos
STATIC_FOLDER = os.path.join(APP_DIR, 'static')  # Carpeta de archivos estáticos
QR_FOLDER = os.path.join(APP_DIR, 'qr')  # Carpeta de códigos QR
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

DATABASE_USER = os.getenv("DB_USER")
DATABASE_PASSWORD = os.getenv("DB_PASSWORD")
DATABASE_HOST = os.getenv("DB_HOST")
DATABASE_NAME = os.getenv("DB_NAME")
DATABASE_PORT = os.getenv("DB_PORT", 3306)
SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

JWT_ACCESS_TOKEN_EXPIRES_IN = parse_date(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_IN")) # 1d
JWT_REFRESH_TOKEN_EXPIRES_IN = parse_date(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_IN")) # 3d