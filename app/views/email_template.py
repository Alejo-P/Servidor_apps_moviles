from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from jinja2 import Template
import os

from app.config.database import get_db
from app.models.users_model import User
from app.middlewares.auth import auth_user
from app.utils.parse import parse_date
from app.config.constants import *
from app.config.settings import settings

view = APIRouter()

@view.get("/email-template", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def get_email_template(
    userInfo: User = Depends(auth_user([ROLE_DEV]))
):
    try:
        template_path = os.path.join(settings.TEMPLATES_FOLDER, "verify_email.html")
        with open(template_path, "r", encoding="utf-8") as file:
            template_content = file.read()

        # Si quieres pasar datos personalizados:
        context = {
            "username": userInfo.name,
            "verify_url": f"{settings.URL_FRONTEND}/#/?verify-email=true&token=fake_token",
            "year": settings.CURRENT_TIME.year
        }

        template = Template(template_content)
        rendered_html = template.render(**context)

        return rendered_html

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al renderizar la plantilla: {str(e)}")
