from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import UserRole
from app.schemas.user import UserOut
from app.utils.validators import (
    clean_display_name,
    clean_email,
    validate_password_strength,
)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    role: UserRole = UserRole.farmer

    @field_validator("email", mode="before")
    @classmethod
    def _normalise_email(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return clean_email(value)

    @field_validator("password", mode="before")
    @classmethod
    def _check_password(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return validate_password_strength(value)

    @field_validator("name", mode="before")
    @classmethod
    def _clean_name(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return clean_display_name(value)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def _normalise_email(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return clean_email(value)


class AuthResponse(BaseModel):
    user: UserOut
    access_token: str
