from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.services.doctor import DoctorService
from app.services.patient import PatientService

SessionDep = Annotated[AsyncSession, Depends(get_session)]


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
