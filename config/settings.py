import os
from dotenv import load_dotenv

load_dotenv()

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