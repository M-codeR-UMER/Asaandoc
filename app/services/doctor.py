from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.doctor import DoctorCreate
from app.database.models import Doctor as DoctorModel
from app.services.base import BaseService
from app.utils import generate_access_token

password_context = CryptContext(schemes="bcrypt")


class DoctorService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(DoctorModel, session)  # type:ignore

    # Users seh joh credentials milien geh unko unkeh model meh add kr keh database meh add krna ha.
    async def add(self, credentials: DoctorCreate) -> DoctorModel:
        new_doctor = DoctorModel(
            **credentials.model_dump(exclude=["password"], exclude_none=True),
            # Applying Hashing here.
            password_hash=password_context.hash(credentials.password),
        )

        return await self._add(new_doctor)

    async def token(self, email, password) -> str:
        result = await self.session.execute(
            select(DoctorModel).where(DoctorModel.email == email)
        )

        doctor = result.scalar_one_or_none()

        if doctor is None or not password_context.verify(
            password, doctor.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Doctor email or password is incorrect",
            )

        token = generate_access_token(
            data={
                "user": {
                    "name": doctor.name,
                    "id": str(doctor.id), # we will include user id here not email(Included) # we convert it to string in order to prevent JSON Object serialization error.
                    "role": "doctor",
                }
            }
        )

        return token
