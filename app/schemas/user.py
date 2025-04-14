from datetime import date, timedelta
from typing import List, Optional

from fastapi import Form
from pydantic import (
    BaseModel,
    EmailStr,
    ValidationInfo,
    field_validator,
)

from app.types.enums import Gender
from app.schemas.story import StorySchema
from app.utils.alpha_validation import (
    is_latin,
    is_cyrillic,
    is_strong_password,
    SPECIAL_CHARS,
)
from app.utils.forms import as_form

MIN_USERNAME_LENGTH = 4
MAX_USERNAME_LENGTH = 20

MIN_AGE = 12
MAX_AGE = 100


def is_age_valid(birth_date: date) -> bool:
    min_date = date.today() - timedelta(days=365.25 * MAX_AGE)
    max_date = date.today() - timedelta(days=365.25 * MIN_AGE)

    if min_date > birth_date or max_date < birth_date:
        return False

    return True


class UserSchemaBase(BaseModel):
    @field_validator("birth_date", check_fields=False)
    @classmethod
    def check_date_of_birth(cls, value: date, info: ValidationInfo) -> date:
        try:
            if isinstance(value, date):
                assert is_age_valid(value), (
                    f"{info.field_name} must be between "
                    f"{MIN_AGE} and {MAX_AGE} years ago"
                )
        except AssertionError as error:
            raise ValueError(error)

        return value

    @field_validator("first_name", "username", "password", check_fields=False)
    @classmethod
    def check_white_space(cls, value: str, info: ValidationInfo) -> str:
        if isinstance(value, str):
            if any(i.isspace() for i in value):
                raise ValueError(f"{info.field_name} must not contain spaces")

        return value

    @field_validator("first_name", check_fields=False)
    @classmethod
    def check_first_name(cls, value: str, info: ValidationInfo) -> str:
        try:
            if isinstance(value, str):
                is_name = (
                    is_cyrillic(value)
                    or is_latin(value)
                    and value.replace(" ", "").isalpha()
                )
                assert is_name, (
                    f"{info.field_name} must be either cyrillic or latin and no digits"
                )
        except AssertionError as error:
            raise ValueError(error)

        return value

    @field_validator("username", check_fields=False)
    @classmethod
    def check_username(cls, value: str, info: ValidationInfo) -> str:
        try:
            if isinstance(value, str):
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

    @field_validator(
        "password", "old_password", "new_password", check_fields=False, mode="before"
    )
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


@as_form
class UserCreateSchema(UserSchemaBase):
    first_name: Optional[str | None] = Form(None, examples=["John"])
    username: str = Form(..., examples=["user123"])
    email: EmailStr = Form(..., examples=["user@example.com"])
    birth_date: Optional[date | None] = Form(None, examples=["2001-01-01"])
    gender: Optional[Gender | None] = Form(None, examples=[""])
    password: str = Form(..., examples=["Qwerty123$"])


@as_form
class UserLoginSchema(UserSchemaBase):
    login: str | EmailStr = Form(..., examples=["user123"])
    password: str = Form(..., examples=["Qwerty123$"])


@as_form
class UserChangeSchema(UserSchemaBase):
    first_name: Optional[str | None] = Form(None, examples=["Kurt"])
    username: Optional[str] = Form(None, examples=["nirvana123"])
    birth_date: Optional[date] = Form(None, examples=["2001-01-01"])
    gender: Optional[Gender | None] = Form(None, examples=["male"])
    description: Optional[str] = Form(
        None, examples=["I'm so happy, 'cause today I found my friends"]
    )


@as_form
class UserChangePasswordSchema(BaseModel):
    old_password: str = Form(..., examples=["Qwerty123$"])
    new_password: str = Form(..., examples=["Qwerty123$"])


@as_form
class UserDeleteSchema(BaseModel):
    password: str = Form(..., examples=["Qwerty123$"])


class UserSchemaPublic(UserSchemaBase):
    id: int
    first_name: Optional[str]
    username: str
    description: Optional[str]
    stories: List[StorySchema] = []
    photo: Optional[bytes]

    class Config:
        from_attributes = True


class UserSchema(UserSchemaPublic):
    email: EmailStr
    birth_date: Optional[date]
    gender: Optional[Gender]

    class Config:
        from_attributes = True
