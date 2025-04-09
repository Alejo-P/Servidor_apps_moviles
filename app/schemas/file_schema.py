from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FileSchema(BaseModel):
    id: int
    filename: str
    filepath: str
    file_size: int
    file_type: str
    uploaded_at: datetime
    uploaded_by: int
    qr_code: Optional[int] = None

    class Config:
        orm_mode = True  # Esto es vital para convertir SQLAlchemy → Pydantic