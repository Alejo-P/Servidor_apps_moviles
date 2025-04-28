import os
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config.settings import settings
from app.controllers import files_controller, qr_controller, auth_controller
from app.middlewares.logging_middleware import RequestLoggerMiddleware
from app.config.database import Base, engine
import app.services.cloudinary_config  # Configuración de Cloudinary (No borrar esta línea)
from app.auth import jwt # Configuración de JWT (No borrar esta línea)

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

# Configurar el middleware de logging
#app.add_middleware(RequestLoggerMiddleware)

# Rutas de la API
app.include_router(files_controller.router, prefix="/api/v1")
app.include_router(qr_controller.router, prefix="/api/v1")
app.include_router(auth_controller.router, prefix="/api/v1")
# app.include_router(files_view.router, prefix="/views")
# app.include_router(home_view.router, prefix="/views")
# app.include_router(qr_view.router, prefix="/views")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(x) for x in err['loc'])
        msg = f"Error en '{loc}': {err['msg']}"
        errors.append(msg)
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors}
    )
    
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={"detail": "Oops! El recurso que buscas no existe. Verifica la URL 🚀"},
        )
    elif exc.status_code == 405:
        return JSONResponse(
            status_code=405,
            content={"detail": "¡Método no permitido! Intenta con otra operación 🤔"},
        )
    else:
        # Para cualquier otro HTTPException que no sea 404 o 405
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )