# app/utils/jwt_handler.py
from datetime import datetime, timedelta
from typing import Optional
import jwt

from app.config.settings import settings
from app.utils.parse import parse_date

def create_access_token(subject: str) -> str:
    expires_delta = timedelta(seconds=int(parse_date(settings.JWT_ACCESS_TOKEN_EXPIRES).total_seconds()))
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": subject,
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, settings.AUTHJWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(subject: str) -> str:
    expires_delta = timedelta(seconds=int(settings.JWT_REFRESH_TOKEN_EXPIRES.total_seconds()))
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": subject,
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(payload, settings.AUTHJWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def verify_token(token: str, token_type: Optional[str] = None) -> dict:
    payload = jwt.decode(token, settings.AUTHJWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    if token_type and payload.get("type") != token_type:
        raise jwt.InvalidTokenError("Tipo de token inválido")
    return payload
