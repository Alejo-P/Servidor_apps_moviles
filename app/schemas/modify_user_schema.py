from pydantic import BaseModel

class ModifyUserSchema(BaseModel):
    user_id: int
    reason: str