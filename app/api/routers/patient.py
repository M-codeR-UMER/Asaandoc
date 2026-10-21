from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import PatientServiceDep, get_access_token
from app.api.schemas.patient import PatientCreate, PatientRead
from app.database.redis import add_jti_to_blacklist

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
    request_form: Annotated[
        OAuth2PasswordRequestForm, Depends()
    ],  # the request body (jason obj)
    service: PatientServiceDep,
):  
    token = await service.token(request_form.username, request_form.password)
    return {
        "access_token": token,
        "type": "jwt",
    }


### Logout
# we need a token_data from access_token_dependency for putting it label to id and than add it to redis database.
@router.post("/logout")
async def logout_patient(
    token_data: Annotated[dict, Depends(get_access_token)],
):
    await add_jti_to_blacklist(token_data["jti"])
    return {"detail": "Successfully logged out"}