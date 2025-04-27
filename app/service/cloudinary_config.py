import cloudinary
import cloudinary.uploader
import cloudinary.api
from app.config.settings import settings

# Configuración inicial
cloudinary.config(
  cloud_name = settings.CLOUDINARY_CLOUD_NAME,  # Nombre de tu nube 
  api_key = settings.CLOUDINARY_API_KEY,  # Clave de API
  api_secret = settings.CLOUDINARY_API_SECRET,  # Secreto de API
  secure = True  # Asegura URLs HTTPS
)
