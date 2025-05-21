from fastapi.security import APIKeyCookie
from fastapi import Security

# Este es tu esquema de seguridad para cookies
cookie_scheme = APIKeyCookie(name="access_token", auto_error=False)
