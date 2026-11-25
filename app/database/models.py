# This files tells us about the things to store in the database models or only the things to store in the database !

from datetime import datetime, timezone
from enum import Enum
import uuid

from pydantic import EmailStr
from sqlalchemy import Column, text
from sqlmodel import DateTime, Field, SQLModel


class MaritalStatus(str, Enum):  # Enum is used for validations.
    SINGLE = "Single"
    MARRIED = "Married"
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

    email: EmailStr = Field(unique=True, index=True)

    password_hash: str

    name: str | None = Field(min_length=1, max_length=32)

    phone_number: str | None = Field(default=None, max_length=20)

    age: int | None = Field(default=None, ge=18)

    gender: Gender | None = Field(default=None)

    marital_status: MaritalStatus | None = Field(default=None)

    terms_accepted_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    terms_version: str | None = Field(default=None, max_length=50)

    email_verified: bool = Field(
        default=False,
        sa_column_kwargs={"server_default": text("false")},
    )

    mfa_enabled: bool = Field(
        default=True,
        sa_column_kwargs={"server_default": text("true")},
    )

    is_active: bool = Field(
        default=True,
        sa_column_kwargs={"server_default": text("true")},
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=text("now()"),
        ),
    )


class Patient(SQLModel, table=True):
    __tablename__ = "patient"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str | None = Field(min_length=1, max_length=32)
    phone_number: str = Field(unique=True, index=True, max_length=20)
    email: EmailStr | None = Field(default=None, nullable=True)
    password_hash: str
    city: str = Field(
        default="Lahore",
        max_length=50,
        sa_column_kwargs={"server_default": text("'Lahore'")},
    )
    age: int | None = Field(default=None, ge=0, le=120)
    gender: Gender | None = Field(default=None)
    marital_status: MaritalStatus | None = Field(default=None)
    terms_accepted_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    terms_version: str | None = Field(default=None, max_length=50)
    is_active: bool = Field(
        default=True,
        sa_column_kwargs={"server_default": text("true")},
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=text("now()"),
        ),
    )


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True)
    role: str = Field(max_length=20)
    token_hash: str = Field(unique=True, index=True, max_length=128)
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    max_expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    revoked_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=text("now()"),
        ),
    )
