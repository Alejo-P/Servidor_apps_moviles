from fastapi import Form
from pydantic import BaseModel
from typing import Optional

class QRCodeSchema(BaseModel):
    name: Optional[str] = None
    text: str

    @classmethod
    def as_form(cls,
                text: str = Form(...),
                name: Optional[str] = Form(None)):
        return cls(name=name, text=text)