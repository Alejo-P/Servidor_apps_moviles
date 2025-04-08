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
        anystr_strip_whitespace = True # Elimina espacios en blanco al inicio y al final de las cadenas
        use_enum_values = True # Convierte los valores de los enums a sus valores en lugar de sus nombres
        allow_population_by_field_name = True # Permite la población de campos por su nombre en lugar de su alias