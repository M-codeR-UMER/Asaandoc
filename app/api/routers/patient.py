from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import (
    AuthServiceDep,
    PatientDep,
    PatientServiceDep,
    get_access_token_patient,
)
from app.api.schemas.auth import LogoutRequest, MessageResponse, TokenResponse
from app.api.schemas.patient import PatientCreate, PatientRead
from app.database.redis import add_jti_to_blacklist

router = APIRouter(prefix="/patient", tags=["Patient"])


@router.post("/signup", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
async def register_patient(
    patient: PatientCreate,
    service: PatientServiceDep,
):
    return await service.add(patient)


@router.post("/token", response_model=TokenResponse)
async def login_patient(
    request_form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: PatientServiceDep,
):
    return await service.token(request_form.username, request_form.password)


@router.post("/logout", response_model=MessageResponse)
async def logout_patient(
    token_data: Annotated[dict, Depends(get_access_token_patient)],
    auth_service: AuthServiceDep,
    payload: LogoutRequest | None = Body(default=None),
):
    await add_jti_to_blacklist(token_data["jti"], token_data["exp"])
    await auth_service.revoke_refresh_token(
        user_id=UUID(token_data["user"]["id"]),
        role="patient",
        raw_token=payload.refresh_token if payload else None,
    )
    return MessageResponse(detail="Successfully logged out")


@router.get("/dashboard", response_model=PatientRead)
async def get_dashboard(patient: PatientDep):
    return patient
