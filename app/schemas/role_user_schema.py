from pydantic import BaseModel

class RoleUserSchema(BaseModel):
    role_name: str
    user_id: int