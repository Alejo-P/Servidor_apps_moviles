import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.controllers import files_controller, qr_controller, auth_controller
#from app.views import files_view, home_view, qr_view
from app.config.database import Base, engine
from app.auth import jwt

from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Crear carpetas necesarias si no existen
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(settings.QR_FOLDER, exist_ok=True)

# Inicializar la base de datos
Base.metadata.create_all(bind=engine)

# Crear la aplicación FastAPI
app = FastAPI(
    title="DocTools API",
    description="API para la gestión de documentos y códigos QR",
    version="1.0.0",
    docs_url="/docs",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia esto por los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas de la API
app.include_router(files_controller.router, prefix="/api/v1")
app.include_router(qr_controller.router, prefix="/api/v1")
app.include_router(auth_controller.router, prefix="/api/v1")
# app.include_router(files_view.router, prefix="/views")
# app.include_router(home_view.router, prefix="/views")
# app.include_router(qr_view.router, prefix="/views")