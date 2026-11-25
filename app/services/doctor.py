from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.auth import TokenResponse
from app.api.schemas.doctor import DoctorCreate
from app.config import security_settings
from app.database.models import Doctor as DoctorModel
from app.services.auth import AuthService
from app.services.base import BaseService
from app.utils import generate_access_token

password_context = CryptContext(schemes="bcrypt")


class DoctorService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(DoctorModel, session)  # type:ignore

    async def add(self, credentials: DoctorCreate) -> DoctorModel:
        normalized_email = str(credentials.email).strip().lower()
        existing = await self.session.execute(
            select(DoctorModel).where(func.lower(DoctorModel.email) == normalized_email)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email or phone already exists.",
            )

        new_doctor = DoctorModel(
            **credentials.model_dump(
                exclude={"password", "terms_accepted"},
                exclude_none=True,
            ),
            password_hash=password_context.hash(credentials.password),
            terms_accepted_at=datetime.now(timezone.utc),
            terms_version="v1",
        )
        new_doctor.email = normalized_email

        try:
            return await self._add(new_doctor)
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email or phone already exists.",
            ) from exc

    async def token(self, email: str, password: str) -> TokenResponse:
        normalized_email = email.strip().lower()
        result = await self.session.execute(
            select(DoctorModel).where(func.lower(DoctorModel.email) == normalized_email)
        )
        doctor = result.scalar_one_or_none()

        if doctor is None or not password_context.verify(
            password, doctor.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Doctor email or password is incorrect",
            )

        if not doctor.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor account is deactivated",
            )

        access_ttl = timedelta(minutes=security_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = generate_access_token(
            data={
                "user": {
                    "name": doctor.name,
                    "id": str(doctor.id),
                    "role": "doctor",
                }
            },
            expiray=access_ttl,
        )
        refresh_token = await AuthService(self.session).create_refresh_token(
            user_id=doctor.id,
            role="doctor",
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_ttl.total_seconds()),
            role="doctor",
        )
