from pydantic import BaseModel

class RegisterSchema(BaseModel):
    name: str
    email: str
    password: str