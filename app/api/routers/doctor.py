from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import DoctorServiceDep, SessionDep, get_access_token_doctor
from app.api.schemas.doctor import DoctorCreate, DoctorRead
from app.core.security import oauth2_scheme_doctor
from app.database.models import Doctor as DoctorModel
from app.database.redis import add_jti_to_blacklist, is_jti_blacklisted
from app.utils import decode_access_token

router = APIRouter(prefix="/doctor", tags=["Doctor"])


### Register a Doctor
@router.post("/signup", response_model=DoctorRead, status_code=status.HTTP_201_CREATED)
async def register_doctor(
    doctor: DoctorCreate,  # the Request model (jason obj)
    service: DoctorServiceDep,
):
    return await service.add(doctor)


### login
@router.post("/token")
async def login_doctor(
    request_form: Annotated[
        OAuth2PasswordRequestForm, Depends()
    ],  # the request body (jason obj)
    service: DoctorServiceDep,
):
    token = await service.token(request_form.username, request_form.password)

    return {
        "access_token": token,
        "token_type": "bearer",
    }


### Logout
@router.post("/logout")
async def logout_doctor(
    token_data: Annotated[dict, Depends(get_access_token_doctor)]
):
    await add_jti_to_blacklist(token_data["jti"], token_data["exp"])
    return {"detail": "Successfully logged out"}
    

### Get Dashboard
@router.get("/dashboard")
async def get_dashboard(
    token_data: Annotated[str, Depends(oauth2_scheme_doctor)],
    session: SessionDep,
) -> DoctorModel:
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

    doctor = await session.get(DoctorModel, UUID(data["user"]["id"]))

    if doctor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found",
            )

    return doctor