from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
)

from app.core.phone import normalize_pakistani_phone, validate_password_strength
from app.database.models import Gender, MaritalStatus

Name = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=32),
]


class BasePatient(BaseModel):
    name: Name
    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        return normalize_pakistani_phone(value)


class PatientCreate(BasePatient):
    password: str
    terms_accepted: Literal[True]
    city: str = Field(default="Lahore", min_length=1, max_length=50)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)


class PatientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str | None = None
    phone_number: str
    email: EmailStr | None = None
    city: str = "Lahore"
    is_active: bool = True


class PatientForm(BaseModel):
    age: int | None
    gender: Gender | None
    marital_status: MaritalStatus | None
