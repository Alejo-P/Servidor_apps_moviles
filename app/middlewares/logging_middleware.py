import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp
from app.utils.logger import get_logger

class RequestLoggerMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger()
        self.excluded_paths = ["/login", "/refresh", "/files/view", "/files/download"]
        self.sensitive_keys = {"password", "token", "secret", "authorization", "cookie", "csrf_access_token", "csrf_refresh_token"}

    async def dispatch(self, request: Request, call_next):
        if any(path in request.url.path for path in self.excluded_paths):
            return await call_next(request)

        # Leer y guardar el body del request
        body_bytes = await request.body()
        body_str = ""
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body_json = json.loads(body_bytes)
                # Ocultar campos sensibles
                sanitized = {
                    key: ("***" if key.lower() in self.sensitive_keys else value)
                    for key, value in body_json.items()
                }
                body_str = json.dumps(sanitized)
            except Exception:
                body_str = "<no se pudo parsear el body>"

        self.logger.info(f"{request.method} {request.url.path} - Headers: {dict(request.headers)}")
        if body_str:
            self.logger.debug(f"Request Body: {body_str}")

        # Restaurar el body para FastAPI
        async def receive():
            return {"type": "http.request", "body": body_bytes, "more_body": False}
        request._receive = receive

        # Capturar y clonar la respuesta
        response = await call_next(request)
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        try:
            decoded_response = response_body.decode('utf-8')
            if "application/json" in (response.media_type or ""):
                self.logger.debug(f"Response Body: {decoded_response}")
            else:
                self.logger.debug("Response Body: <omitido por no ser texto>")
        except Exception:
            self.logger.debug("Response Body: <no se pudo decodificar>")

        self.logger.info(f"Response Status: {response.status_code}")

        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )
