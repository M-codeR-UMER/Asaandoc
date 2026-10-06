from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import PatientServiceDep
from app.api.schemas.patient import PatientCreate, PatientRead
from app.core.security import oauth2_scheme
from app.utils import decode_access_token

router = APIRouter(prefix="/patient", tags=["Patient"])


### Register a Patient
@router.post("/signup", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
async def register_patient(
    patient: PatientCreate,  # the Request model (jason obj)
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


### Get Dashboard
@router.get("/dashboard")
def Dashboard(token: Annotated[str, Depends(oauth2_scheme)]):
    # return {"Authorized": True}
    data = decode_access_token(token=token)

    if data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=" Invalid Access Token"
        )

    return {
        "detail" : "Successfully Authenticated !"
    }

### Logout
@router.post("/logout")
async def logout_patient():
    pass
