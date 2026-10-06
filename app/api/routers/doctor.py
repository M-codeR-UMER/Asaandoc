from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import DoctorServiceDep
from app.api.schemas.doctor import DoctorCreate, DoctorRead

router = APIRouter(prefix="/doctor", tags=["Doctor"])


### Register a Doctor
@router.post("/signup", response_model=DoctorRead, status_code=status.HTTP_201_CREATED)
async def register_doctor(
    doctor: DoctorCreate, # the Request model (jason obj)
    service: DoctorServiceDep,
):
    return await service.add(doctor)


### login
@router.post("/token")
async def login_doctor(
    request_form: Annotated[  # the request body (jason obj)
        OAuth2PasswordRequestForm, Depends()
    ],
):
    pass


### Logout
@router.post("/logout")
async def logout_doctor():
    pass
