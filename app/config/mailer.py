from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.config.settings import settings

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
    TEMPLATE_FOLDER='app/templates'
)

async def send_email_async(subject: str, email_to: str, body: dict, template_name: str = 'email.html'):
    """
    Send an email asynchronously using FastAPI Mail.
    """
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
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        template_body=body,
        subtype='html',
    )
    
    fm = FastMail(mail_conf)
    background_tasks.add_task(fm.send_message, message, template_name=template_name)