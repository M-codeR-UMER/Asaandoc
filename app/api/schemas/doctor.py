from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    StringConstraints,
    field_validator,
)

from app.core.phone import normalize_pakistani_phone, validate_password_strength
from app.database.models import Gender, MaritalStatus

Name = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=32),
]


class BaseDoctor(BaseModel):
    name: Name
    email: EmailStr


class DoctorCreate(BaseDoctor):
    phone_number: str
    password: str
    terms_accepted: Literal[True]

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        return normalize_pakistani_phone(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)


class DoctorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str | None = None
    email: EmailStr
    phone_number: str | None = None
    email_verified: bool = False
    mfa_enabled: bool = True
    is_active: bool = True


class DoctorForm(BaseModel):
    age: int | None
    gender: Gender | None
    marital_status: MaritalStatus | None
