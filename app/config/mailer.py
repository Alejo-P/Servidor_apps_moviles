from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from colorama import Fore, Style
from urllib.parse import urlencode
from app.config.constants import *
from app.config.settings import settings

def _get_url_template(template_name: str, **kwargs):
    """
    Generate a URL for the email template with query parameters.
    """
    query_params = urlencode(kwargs)
    base_url = f"{settings.URL_BACKEND + settings.API_V1_STR}/render-template/{template_name}?{query_params}"
    return base_url

mail_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER=settings.EMAIL_TEMPLATES_FOLDER
)

async def send_email_async(subject: str, email_to: str, body: dict, template_name: str = 'email.html'):
    """
    Send an email asynchronously using FastAPI Mail.
    """
    # Para entornos de desarrollo, no se envía el correo
    if settings.ENV == ENV_DEVELOPMENT:
        print(f"[DEV] Simulando envío de correo a: {email_to}")
        print(f"[DEV] Asunto: {subject}")
        print(f"[DEV] Cuerpo: {body}")
        # Aqui se puede renderizar la vista del correo
        # Generar la URL de la plantilla con los parámetros de consulta
        data = {
            "subject": subject,
            "email_to": email_to,
            **body
        }
        url_template = _get_url_template(template_name, **data)
        print(f"[DEV] Vista renderizada del correo: {url_template}")
        return
    
    # Para entornos de producción, se envía el correo
    # Se crea el mensaje
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        template_body=body,
        subtype='html',
    )
    
    fm = FastMail(mail_conf)
    await fm.send_message(message, template_name=template_name)

def send_email_background(background_tasks: BackgroundTasks, subject: str, email_to: str, body: dict, template_name: str = 'email.html'):
    """
    Send an email in the background using FastAPI's BackgroundTasks.
    """
    # Para entornos de desarrollo, no se envía el correo
    if settings.ENV == ENV_DEVELOPMENT:
        print(Fore.GREEN + f"[DEV] Simulando envío de correo a: {email_to}" + Style.RESET_ALL)
        print(Fore.GREEN + f"[DEV] Asunto: {subject}" + Style.RESET_ALL)
        print(Fore.GREEN + f"[DEV] Cuerpo: {body}" + Style.RESET_ALL)
        # Aqui se puede renderizar la vista del correo
        # Generar la URL de la plantilla con los parámetros de consulta
        
        data = {
            "subject": subject,
            "email_to": email_to,
            **body
        }
        url_template = _get_url_template(template_name, **data)

        print(Fore.YELLOW + f"[DEV] Vista renderizada del correo: {url_template}" + Style.RESET_ALL)
        return
    
    # Para entornos de producción, se envía el correo
    # Se crea el mensaje
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        template_body=body,
        subtype='html',
    )
    
    fm = FastMail(mail_conf)
    background_tasks.add_task(fm.send_message, message, template_name=template_name)