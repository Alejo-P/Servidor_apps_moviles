from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel
from config.settings import settings

class JWTSettings(BaseModel):
    authjwt_secret_key: str = settings.JWT_SECRET_KEY
    authjwt_algorithm: str = settings.JWT_ALGORITHM
    authjwt_access_token_expires: int = settings.JWT_ACCESS_TOKEN_EXPIRES

@AuthJWT.load_config
def get_config():
    return JWTSettings()
