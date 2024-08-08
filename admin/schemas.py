from pydantic import BaseModel, EmailStr, Field


class AdminBaseSchema(BaseModel):
    email: EmailStr


class AdminCreateSchema(AdminBaseSchema):
    hashed_password: str = Field(alias="password")
