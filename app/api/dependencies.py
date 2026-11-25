from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import oauth2_scheme_doctor, oauth2_scheme_patient
from app.database.models import Doctor as DoctorModel
from app.database.models import Patient
from app.database.redis import is_jti_blacklisted
from app.database.session import get_session
from app.services.auth import AuthService
from app.services.doctor import DoctorService
from app.services.patient import PatientService
from app.utils import decode_access_token

# Async Database Session Dependency
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def _validate_role_token(token: str, expected_role: str) -> dict:
    data = decode_access_token(token=token)
    if (
        data is None
        or not data.get("jti")
        or await is_jti_blacklisted(data["jti"])
        or data.get("user", {}).get("role") != expected_role
        or not data.get("user", {}).get("id")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Access Token",
        )
    return data


# Patient Access token data dep
async def get_access_token_patient(
    token: Annotated[str, Depends(oauth2_scheme_patient)],
) -> dict:
    return await _validate_role_token(token, "patient")


# Logged In Patient Dep (Current Patient Dep)
async def get_logged_in_patient(
    token_data: Annotated[dict, Depends(get_access_token_patient)],
    session: SessionDep,
) -> Patient:
    patient = await session.get(Patient, UUID(token_data["user"]["id"]))

    if patient is None or not patient.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Patient not found",
        )

    return patient


# Current Patient Dep
PatientDep = Annotated[Patient, Depends(get_logged_in_patient)]


# Doctor Access token data dep
async def get_access_token_doctor(
    token: Annotated[str, Depends(oauth2_scheme_doctor)],
) -> dict:
    return await _validate_role_token(token, "doctor")


# Logged In Doctor Dep (Current Doctor Dep)
async def get_logged_in_doctor(
    token_data: Annotated[dict, Depends(get_access_token_doctor)],
    session: SessionDep,
) -> DoctorModel:
    doctor = await session.get(DoctorModel, UUID(token_data["user"]["id"]))

    if doctor is None or not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Doctor not found",
        )

    return doctor


# Current Doctor Dep
DoctorDep = Annotated[DoctorModel, Depends(get_logged_in_doctor)]


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)


def get_patient_service(session: SessionDep) -> PatientService:
    return PatientService(session)


def get_doctor_service(session: SessionDep) -> DoctorService:
    return DoctorService(session)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
PatientServiceDep = Annotated[PatientService, Depends(get_patient_service)]
DoctorServiceDep = Annotated[DoctorService, Depends(get_doctor_service)]
