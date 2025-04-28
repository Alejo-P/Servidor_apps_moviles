from pydantic import BaseModel
from fastapi import Form

class AvatarUploadForm(BaseModel):
    user_id: str

    @classmethod
    def as_form(
        cls,
        user_id: str = Form(...),
    ):
        return cls(user_id=user_id)
