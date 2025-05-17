import base64
import hashlib
import hmac
from datetime import timedelta

from app.config.settings import settings


def create_verification_token(secret_key: str, email: str, expires_in_minutes: int = 60) -> str:
    expires_at = (settings.CURRENT_TIME + timedelta(minutes=expires_in_minutes)).timestamp()
    expires_at_str = str(int(expires_at))

    message = f"{email}:{expires_at_str}"
    hmac_obj = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256)
    signature = base64.urlsafe_b64encode(hmac_obj.digest()).decode()

    return f"{signature}:{expires_at_str}"


def verify_email_token(secret_key: str, token: str, email: str) -> bool:
    try:
        signature, expires_at_str = token.split(":")
        expires_at = int(expires_at_str)
    except (ValueError, TypeError):
        return False

    if settings.CURRENT_TIME.timestamp() > expires_at:
        return False  # Token expirado

    expected_message = f"{email}:{expires_at_str}"
    expected_hmac = hmac.new(secret_key.encode(), expected_message.encode(), hashlib.sha256)
    expected_signature = base64.urlsafe_b64encode(expected_hmac.digest()).decode()

    return hmac.compare_digest(signature, expected_signature)


