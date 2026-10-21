from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import oauth2_scheme
from app.database.models import Patient
from app.database.redis import is_jti_blacklisted
from app.database.session import get_session
from app.services.doctor import DoctorService
from app.services.patient import PatientService
from app.utils import decode_access_token

# Async Database Session Dependency
SessionDep = Annotated[AsyncSession, Depends(get_session)]


# Access token data dep
async def get_access_token(token: Annotated[str, Depends(oauth2_scheme)]):
    data = decode_access_token(token=token)

    # Validating the token
    if data is None or await is_jti_blacklisted(data["jti"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=" Invalid Access Token",
        )

    return data


# Logged In Patient Dep
async def get_logged_in_patient(
    token_data: Annotated[dict, Depends(get_access_token)],
    session: SessionDep,
):
    return await session.get(Patient, token_data["data"]["user"]["id"])  # Error


# Patient Service Getter
def get_patient_service(session: SessionDep):
    return PatientService(session)


# Doctor Service Getter
def get_doctor_service(session: SessionDep):
    return DoctorService(session)


# Patient Service Dep
PatientServiceDep = Annotated[PatientService, Depends(get_patient_service)]

# Doctor Service Dep
DoctorServiceDep = Annotated[DoctorService, Depends(get_doctor_service)]

# Current Patient Dep
PatientDep = Annotated[Patient, Depends(get_logged_in_patient)]
