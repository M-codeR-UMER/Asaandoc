from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import (
    AuthServiceDep,
    DoctorDep,
    DoctorServiceDep,
    get_access_token_doctor,
)
from app.api.schemas.auth import LogoutRequest, MessageResponse, TokenResponse
from app.api.schemas.doctor import DoctorCreate, DoctorRead
from app.database.redis import add_jti_to_blacklist

router = APIRouter(prefix="/doctor", tags=["Doctor"])


@router.post("/signup", response_model=DoctorRead, status_code=status.HTTP_201_CREATED)
async def register_doctor(
    doctor: DoctorCreate,
    service: DoctorServiceDep,
):
    return await service.add(doctor)


@router.post("/token", response_model=TokenResponse)
async def login_doctor(
    request_form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: DoctorServiceDep,
):
    return await service.token(request_form.username, request_form.password)


@router.post("/logout", response_model=MessageResponse)
async def logout_doctor(
    token_data: Annotated[dict, Depends(get_access_token_doctor)],
    auth_service: AuthServiceDep,
    payload: LogoutRequest | None = Body(default=None),
):
    await add_jti_to_blacklist(token_data["jti"], token_data["exp"])
    await auth_service.revoke_refresh_token(
        user_id=UUID(token_data["user"]["id"]),
        role="doctor",
        raw_token=payload.refresh_token if payload else None,
    )
    return MessageResponse(detail="Successfully logged out")


@router.get("/dashboard", response_model=DoctorRead)
async def get_dashboard(doctor: DoctorDep):
    return doctor
