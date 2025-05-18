from pydantic import BaseModel, EmailStr, Field

class VerifyEmailSchema(BaseModel):
    email: EmailStr = Field(
        ...,
        description="The email address to verify",
        example="user@example.com"
    )
    token: str = Field(
        ...,
        description="The verification token sent to the email address",
        example="1234567890abcdef"
    )