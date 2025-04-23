from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import get_logger

class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger = get_logger()
        logger.info(f"{request.method} {request.url.path} - Headers: {dict(request.headers)}")
        if request.method in ("POST", "PUT", "PATCH"):
            body = await request.body()
            logger.debug(f"Body: {body.decode('utf-8')}")
        response = await call_next(request)
        logger.info(f"Response Status: {response.status_code}")
        return response
