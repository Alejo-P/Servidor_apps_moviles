from fastapi import APIRouter, Depends, HTTPException, status, Request
from werkzeug.utils import secure_filename
from fastapi.responses import HTMLResponse
from jinja2 import Template
import os

from app.config.database import get_db
from app.models.users_model import User
from app.middlewares.auth import auth_user
from urllib.parse import quote
from app.config.constants import *
from app.config.settings import settings
from app.utils.verif_token import create_secure_token, verify_secure_token

view = APIRouter()

@view.get("/email-template/{template_name}", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def get_email_template(
    template_name: str,
    userInfo: User = Depends(auth_user([ROLE_DEV]))
):
    try:
        file_name = secure_filename(template_name)
        if not file_name.endswith(".html"):
            raise HTTPException(status_code=400, detail="El archivo debe ser un HTML")
        
        if not os.path.exists(settings.EMAIL_TEMPLATES_FOLDER):
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        # Cargar la plantilla HTML
        template_path = os.path.join(settings.EMAIL_TEMPLATES_FOLDER, file_name)
        if not os.path.exists(template_path):
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        # Leer el contenido de la plantilla
        with open(template_path, "r", encoding="utf-8") as file:
            template_content = file.read()
            
        # Crear un token de verificación (solo para el ejemplo)
        token = create_secure_token(settings.SECRET_KEY, userInfo.email, expires_in_minutes=1)

        # Si quieres pasar datos personalizados:
        context = {
            "username": userInfo.name,
            "verify_url": f"{settings.URL_FRONTEND}/#/?verify-email=true&token={quote(token)}",
            "year": settings.CURRENT_TIME.year
        }

        template = Template(template_content)
        rendered_html = template.render(**context)

        return rendered_html

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    except Exception as e:
        # Manejo de errores al renderizar la plantilla (si es HTTPException, devuelve el error)
        if isinstance(e, HTTPException):
            raise e
        else:
            raise HTTPException(status_code=500, detail=f"Error al renderizar la plantilla: {str(e)}")
        
        
@view.get("/render-template/{template_name}", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def render_template(
    template_name: str,
    request: Request,
    userInfo: User = Depends(auth_user([ROLE_DEV]))
):
    try:
        print("Entrando a render_template")
        print(f"template_name: {template_name}")
        print(f"request: {request}")
        file_name = secure_filename(template_name)
        if not file_name.endswith(".html"):
            raise HTTPException(status_code=400, detail="El archivo debe ser un HTML")

        if not os.path.exists(settings.EMAIL_TEMPLATES_FOLDER):
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")

        template_path = os.path.join(settings.EMAIL_TEMPLATES_FOLDER, file_name)
        if not os.path.exists(template_path):
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")

        with open(template_path, "r", encoding="utf-8") as file:
            template_content = file.read()

        context = dict(request.query_params)

        template = Template(template_content)
        rendered_html = template.render(**context)
        return rendered_html
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")