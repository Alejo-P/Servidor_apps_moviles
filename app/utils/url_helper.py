from fastapi import Request

def base_url(request: Request, path: str = "") -> str:
    """
    Retorna la URL base de la aplicación con un path opcional.
    Ejemplo:
        base_url(request) -> http://127.0.0.1:8000/
        base_url(request, "login") -> http://127.0.0.1:8000/login
    """
    return str(request.base_url) + path.lstrip("/")
