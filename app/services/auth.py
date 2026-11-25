import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.auth import TokenResponse
from app.config import security_settings
from app.database.models import Doctor, Patient, RefreshToken
from app.utils import generate_access_token


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _refresh_ttl_for_role(role: str) -> timedelta:
    if role == "doctor":
        return timedelta(hours=security_settings.DOCTOR_REFRESH_MAX_HOURS)
    return timedelta(days=security_settings.PATIENT_REFRESH_DAYS)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_refresh_token(
        self,
        *,
        user_id: UUID,
        role: Literal["doctor", "patient", "admin"],
    ) -> str:
        raw_token = secrets.token_urlsafe(48)
        now = datetime.now(timezone.utc)
        expires_at = now + _refresh_ttl_for_role(role)

        record = RefreshToken(
            user_id=user_id,
            role=role,
            token_hash=hash_refresh_token(raw_token),
            expires_at=expires_at,
            max_expires_at=expires_at,
        )
        self.session.add(record)
        await self.session.commit()
        return raw_token

    async def refresh(self, raw_token: str) -> TokenResponse:
        token_hash = hash_refresh_token(raw_token)
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        record = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if record is None or record.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked refresh token",
            )

        expires_at = _ensure_utc(record.expires_at)
        max_expires_at = _ensure_utc(record.max_expires_at)
        if now >= expires_at or now >= max_expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
            )

        user_name: str | None = None
        if record.role == "doctor":
            doctor = await self.session.get(Doctor, record.user_id)
            if doctor is None or not doctor.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Doctor account is inactive or not found",
                )
            user_name = doctor.name
        elif record.role == "patient":
            patient = await self.session.get(Patient, record.user_id)
            if patient is None or not patient.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Patient account is inactive or not found",
                )
            user_name = patient.name
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unsupported token role",
            )

        record.revoked_at = now

        new_raw_token = secrets.token_urlsafe(48)
        ttl = _refresh_ttl_for_role(record.role)
        new_expires_at = min(now + ttl, max_expires_at)

        rotated = RefreshToken(
            user_id=record.user_id,
            role=record.role,
            token_hash=hash_refresh_token(new_raw_token),
            expires_at=new_expires_at,
            max_expires_at=max_expires_at,
        )
        self.session.add(rotated)
        await self.session.commit()

        access_ttl = timedelta(minutes=security_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        if record.role == "doctor":
            remaining = max_expires_at - now
            if remaining < access_ttl:
                access_ttl = remaining

        access_token = generate_access_token(
            data={
                "user": {
                    "name": user_name,
                    "id": str(record.user_id),
                    "role": record.role,
                }
            },
            expiray=access_ttl,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_raw_token,
            token_type="bearer",
            expires_in=int(access_ttl.total_seconds()),
            role=record.role,  # type: ignore[arg-type]
        )

    async def revoke_refresh_token(
        self,
        *,
        user_id: UUID,
        role: str,
        raw_token: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.role == role,
                RefreshToken.revoked_at.is_(None),  # type: ignore[union-attr]
            )
            .values(revoked_at=now)
        )
        if raw_token:
            stmt = stmt.where(RefreshToken.token_hash == hash_refresh_token(raw_token))

        await self.session.execute(stmt)
        await self.session.commit()
