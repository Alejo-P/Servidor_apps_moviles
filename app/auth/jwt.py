from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel
from app.config.settings import settings
from app.utils.parse import parse_date

class JWTSettings(BaseModel):
    authjwt_secret_key: str = settings.AUTHJWT_SECRET_KEY
    authjwt_algorithm: str = settings.JWT_ALGORITHM
    authjwt_access_token_expires: int = int(parse_date(settings.JWT_ACCESS_TOKEN_EXPIRES).total_seconds())
    authjwt_refresh_token_expires: int = int(parse_date(settings.JWT_REFRESH_TOKEN_EXPIRES).total_seconds())

@AuthJWT.load_config
def get_config():
    return JWTSettings()
