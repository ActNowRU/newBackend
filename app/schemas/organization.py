from typing import List, Dict, Optional

from fastapi import Form
from pydantic import (
    BaseModel,
    EmailStr,
    ValidationInfo,
    field_validator,
)

from app.types.enums import OrganizationType
from app.schemas.goal import GoalSchema
from app.schemas.story import StorySchema
from app.utils.alpha_validation import is_strong_password, SPECIAL_CHARS
from app.utils.forms import as_form

MIN_NAME_LENGTH = 3
MAX_NAME_LENGTH = 20


class OrganizationSchemaBase(BaseModel):
    @field_validator("name", check_fields=False)
    @classmethod
    def check_username(cls, value: str, info: ValidationInfo) -> str:
        try:
            if isinstance(value, str):
                is_alphanumeric = value.replace(" ", "").isalnum()
                assert is_alphanumeric, f"{info.field_name} must be alphanumeric"
                assert MIN_NAME_LENGTH <= len(value) < MAX_NAME_LENGTH, (
                    f"{info.field_name} must be at least {MIN_NAME_LENGTH} "
                    f"and at most {MAX_NAME_LENGTH} characters long"
                )
        except AssertionError as error:
            raise ValueError(error)

        return value

    @field_validator("password", check_fields=False, mode="before")
    @classmethod
    def check_password(cls, password: str) -> str:
        if not is_strong_password(password):
            raise ValueError(
                "Password must contain at least "
                "one lower character, "
                "one upper character, "
                "one digit and "
                f"one special symbol from {', '.join(SPECIAL_CHARS)}"
            )

        return password


class OrganizationSchema(OrganizationSchemaBase):
    id: int
    name: str
    description: Optional[str]

    common_discount: Optional[int]
    max_discount: Optional[int]

    photo: Optional[bytes]

    goals: List[GoalSchema] = []
    stories: List[StorySchema] = []

    class Config:
        from_attributes = True


@as_form
class OrganizationCreateSchema(OrganizationSchemaBase):
    name: str = Form(...)
    description: Optional[str] = Form(None)

    inn_or_ogrn: str = Form(...)
    legal_address: str = Form(...)

    email: EmailStr = Form(...)

    organization_type: OrganizationType = Form(...)

    password: str = Form(...)


@as_form
class OrganizationChangeSchema(OrganizationSchemaBase):
    name: Optional[str] = Form(None)
    description: Optional[str] = Form(None)

    static_discount: Optional[float] = Form(None)
    common_discount: Optional[float] = Form(None)
    max_discount: Optional[float] = Form(None)

    step_amount: Optional[int] = Form(None)
    days_to_step_back: Optional[int] = Form(None)


@as_form
class SetPlaceLocationSchema(BaseModel):
    name: str
    address: str


class SummaryPlaceSchema(BaseModel):
    id: int
    organization_id: int
    name: str
    address: str
    location: Dict[str, float]

    class Config:
        from_attributes = True


class VerbosePlaceSchema(BaseModel):
    id: int
    organization: OrganizationSchema
    name: str
    address: str
    location: Dict[str, float]
