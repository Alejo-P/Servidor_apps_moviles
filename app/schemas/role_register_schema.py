from pydantic import BaseModel, Field
from typing import Optional, List

class RoleRegisterSchema(BaseModel):
    role_name: str = Field(..., description="Name of the role")
    permissions: List[str] = Field(..., description="List of permissions associated with the role")
    description: Optional[str] = Field(None, description="Description of the role")
    created_at: Optional[str] = Field(None, description="Timestamp when the role was created")
    updated_at: Optional[str] = Field(None, description="Timestamp when the role was last updated")

    class Config:
        schema_extra = {
            "example": {
                "role_name": "Admin",
                "permissions": ["create", "read", "update", "delete"],
                "description": "Administrator role with full access",
                "created_at": "2023-10-01T12:00:00Z",
                "updated_at": "2023-10-01T12:00:00Z"
            }
        }
        orm_mode = True