from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.patient import PatientCreate
from app.database.models import Patient
from app.database.models import Patient as patientmodel
from app.utils import generate_access_token

from .base import BaseService

password_context = CryptContext(schemes="bcrypt")  # for hashing password


class PatientService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(patientmodel, session)  # type: ignore

    async def add(self, credentials: PatientCreate) -> patientmodel:
        new_patient = patientmodel(
            **credentials.model_dump(exclude=["password"], exclude_none=True),
            # Hashed Password
            password_hash=password_context.hash(credentials.password),
        )
        return await self._add(new_patient)

    async def token(self, email, password) -> str:
        # Validate the creadentials
        # Below query will return patient object.
        result = await self.session.execute(
            select(Patient).where(
                Patient.email == email
            )  # Custom Sql query with SQLAlchemy
        )
        patient = result.scalar()

        if not patient or not password_context.verify(password, patient.password_hash):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient email or password is incorrect",
            )

        # Don't include sensitive information here as we had done it below: -
        token = generate_access_token(
            data={
                "user": {
                    "name": patient.name,
                    "email": patient.email,  # we will include user id here not email
                }
            }
        )

        return token
