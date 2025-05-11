from pydantic import BaseModel
from typing import Optional
from pydantic.networks import EmailStr

class UpdateProfileSchema(BaseModel):
    name: str
    email: EmailStr
    
class UpdatePasswordSchema(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "new_password": "new_password",
                "confirm_password": "new_password"
            }
        }