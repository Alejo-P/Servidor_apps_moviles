import base64
import hashlib
import hmac
from datetime import timedelta
from urllib.parse import quote
import json

from app.config.settings import settings

# Funciones para crear y verificar un token seguro
# El token se crea con un payload que contiene el email y la fecha de expiración
# El token se firma con una clave secreta y se codifica en base64
# El token se puede verificar comparando la firma y decodificando el payload
# El payload contiene el email y la fecha de expiración
# El token se puede usar para verificar la dirección de correo electrónico del usuario

def create_secure_token(secret_key: str, email: str, expires_in_minutes: int = 60) -> str:
    payload = {
        "email": email,
        "exp": int((settings.CURRENT_TIME + timedelta(minutes=expires_in_minutes)).timestamp())
    }

    json_payload = json.dumps(payload, separators=(",", ":")).encode()
    b64_payload = base64.urlsafe_b64encode(json_payload).decode()

    signature = hmac.new(secret_key.encode(), b64_payload.encode(), hashlib.sha256)
    b64_signature = base64.urlsafe_b64encode(signature.digest()).decode()

    token = f"{b64_payload}.{b64_signature}"
    return quote(token)  # URL encode final


def verify_secure_token(secret_key: str, token: str) -> dict | None:
    try:
        b64_payload, b64_signature = token.split(".")
        expected_signature = base64.urlsafe_b64encode(
            hmac.new(secret_key.encode(), b64_payload.encode(), hashlib.sha256).digest()
        ).decode()

        if not hmac.compare_digest(expected_signature, b64_signature):
            return None

        json_payload = base64.urlsafe_b64decode(b64_payload).decode()
        payload = json.loads(json_payload)

        if settings.CURRENT_TIME.timestamp() > payload["exp"]:
            return None

        return payload  # Devuelve el email y exp
    except Exception as e:
        return None



