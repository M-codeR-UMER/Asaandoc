# This files tells us about the things to store in the database models or only the things to store in the database !

from enum import Enum
import uuid

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class MaritalStatus(str, Enum):  # Enum is used for validations.
    SINGLE = "Single"
    MARRIED = "Married"
    UNMARRIED = "Unmarried"
    DIVORCED = "Divorced"
    WIDOWED = "Widow"
    OTHERS = "Others"


class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class Doctor(SQLModel, table=True):
    __tablename__ = "doctor"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: EmailStr = Field(unique= True, index=True)
    password_hash: str
    name: str | None = Field(min_length=1, max_length=32)
    # phone_number: PhoneNumber | None = Field(default= None)
    age: int | None = Field(default=None, ge=18)
    gender: Gender | None = Field(default=None)
    marital_status: MaritalStatus | None = Field(default=None)

class Patient(SQLModel, table=True):
    __tablename__ = "patient"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str | None = Field(min_length=1, max_length=32)
    email: EmailStr = Field(unique= True, index=True)
    password_hash: str
    # phone_number: PhoneNumber | None = Field(default= None)
    age: int | None = Field(default=None, ge=0, le=120)
    gender: Gender | None = Field(default=None)
    marital_status: MaritalStatus | None = Field(default=None)
