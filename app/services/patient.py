from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.auth import TokenResponse
from app.api.schemas.patient import PatientCreate
from app.config import security_settings
from app.core.phone import normalize_pakistani_phone
from app.database.models import Patient
from app.services.auth import AuthService
from app.utils import generate_access_token

from .base import BaseService

password_context = CryptContext(schemes="bcrypt")


class PatientService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(Patient, session)  # type: ignore

    async def add(self, credentials: PatientCreate) -> Patient:
        normalized_phone = normalize_pakistani_phone(credentials.phone_number)
        existing = await self.session.execute(
            select(Patient).where(Patient.phone_number == normalized_phone)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this phone number already exists.",
            )

        new_patient = Patient(
            **credentials.model_dump(
                exclude={"password", "terms_accepted"},
                exclude_none=True,
            ),
            password_hash=password_context.hash(credentials.password),
            terms_accepted_at=datetime.now(timezone.utc),
            terms_version="v1",
        )
        new_patient.phone_number = normalized_phone

        try:
            return await self._add(new_patient)
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this phone number already exists.",
            ) from exc

    async def token(self, phone_number: str, password: str) -> TokenResponse:
        try:
            normalized_phone = normalize_pakistani_phone(phone_number)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc

        result = await self.session.execute(
            select(Patient).where(Patient.phone_number == normalized_phone)
        )
        patient = result.scalar_one_or_none()

        if patient is None or not password_context.verify(
            password, patient.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Patient phone number or password is incorrect",
            )

        if not patient.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Patient account is deactivated",
            )

        access_ttl = timedelta(minutes=security_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = generate_access_token(
            data={
                "user": {
                    "name": patient.name,
                    "id": str(patient.id),
                    "role": "patient",
                }
            },
            expiray=access_ttl,
        )
        refresh_token = await AuthService(self.session).create_refresh_token(
            user_id=patient.id,
            role="patient",
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_ttl.total_seconds()),
            role="patient",
        )
