from typing import List, Optional

from fastapi import Form
from pydantic import (
    BaseModel,
    EmailStr,
    ValidationInfo,
    field_validator,
)

from services.database.models.organization import OrganizationType
from services.database.schemas.goal import Goal
from services.database.schemas.story import StoryCreateSchema as Story
from utils.alpha_validation import is_latin, is_strong_password, SPECIAL_CHARS
from utils.forms import as_form

MIN_USERNAME_LENGTH = 4
MAX_USERNAME_LENGTH = 20


class OrganizationSchemaBase(BaseModel):
    @field_validator("username", check_fields=False)
    @classmethod
    def check_username(cls, value: str, info: ValidationInfo) -> str:
        try:
            if isinstance(value, str):
                assert not any(
                    i.isspace() for i in value
                ), f"{info.field_name} must not contain spaces"

                is_alphanumeric = value.replace(" ", "").isalnum()
                assert is_alphanumeric, f"{info.field_name} must be alphanumeric"
                assert is_latin(value), f"{info.field_name} must be latin"
                assert MIN_USERNAME_LENGTH <= len(value) < MAX_USERNAME_LENGTH, (
                    f"{info.field_name} must be at least {MIN_USERNAME_LENGTH} "
                    f"and at most {MAX_USERNAME_LENGTH} characters long"
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
    username: str
    description: Optional[str]

    common_discount: Optional[int]
    max_discount: Optional[int]

    goals: List[Goal] = []
    stories: List[Story] = []

    class Config:
        from_attributes = True


@as_form
class OrganizationCreateSchema(OrganizationSchemaBase):
    username: str = Form(...)

    inn_or_ogrn: str = Form(...)
    legal_address: str = Form(...)

    email: EmailStr = Form(...)

    organization_type: OrganizationType = Form(...)

    password: str = Form(...)


@as_form
class OrganizationChangeSchema(OrganizationSchemaBase):
    username: Optional[str] = Form(None)
    description: Optional[str] = Form(None)
    common_discount: Optional[int] = Form(None)
    max_discount: Optional[int] = Form(None)


@as_form
class SetPlaceLocationSchema(BaseModel):
    lat: float = Form(...)
    lon: float = Form(...)


class PlaceSchema(BaseModel):
    id: int
    address: str
    location: dict

    class Config:
        from_attributes = True
