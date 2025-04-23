from pydantic import BaseModel

class UploadFileSchema(BaseModel):
    filename: str
    filetype: str
    size: int
    filebase64: str