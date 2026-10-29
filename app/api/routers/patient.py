from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import PatientServiceDep, SessionDep, get_access_token_patient
from app.api.schemas.patient import PatientCreate, PatientRead
from app.core.security import oauth2_scheme_patient
from app.database.models import Patient
from app.database.redis import add_jti_to_blacklist, is_jti_blacklisted
from app.utils import decode_access_token

router = APIRouter(prefix="/patient", tags=["Patient"])


### Register a Patient
@router.post("/signup", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
async def register_patient(
    patient: PatientCreate,  # the Request model (jason obj) it do validation here
    service: PatientServiceDep,
):
    return await service.add(patient)


### login
@router.post("/token")
async def login_patient(
    request_form: Annotated[OAuth2PasswordRequestForm, Depends()],  # the request body (jason obj)
    service: PatientServiceDep,
):
    token = await service.token(request_form.username, request_form.password)
    return {
        "access_token": token,
        "token_type": "bearer",
    }


### Logout
# we need a token_data from access_token_dependency for putting it label to id and than add it to redis database.
@router.post("/logout")
async def logout_patient(
    token_data: Annotated[dict, Depends(get_access_token_patient)],
):
    await add_jti_to_blacklist(token_data["jti"], token_data["exp"])
    return {"detail": "Successfully logged out"}


### Get Dashboard
@router.get("/dashboard")
async def get_dashboard(
    token_data: Annotated[str, Depends(oauth2_scheme_patient)],
    session: SessionDep,
):
    data = decode_access_token(token_data)

    if data is None or await is_jti_blacklisted(data["jti"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    if "user" not in data or "id" not in data["user"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token data",
        )
    
    patient = await session.get(Patient, UUID(data["user"]["id"]))

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    return patient