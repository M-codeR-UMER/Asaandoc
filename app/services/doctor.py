from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.doctor import DoctorCreate
from app.database.models import Doctor as DoctorModel
from app.services.base import BaseService

password_context = CryptContext(schemes="bcrypt")


class DoctorService(BaseService):
    def __init__(self,session:AsyncSession):
        super().__init__(DoctorModel, session) #type:ignore

# Users seh joh credentials milien geh unko unkeh model meh add kr keh database meh add krna ha.
    async def add(self, credentials: DoctorCreate) -> DoctorModel:  
        new_doctor = DoctorModel(
            **credentials.model_dump(exclude=["password"],exclude_none= True),
        
            # Applying Hashing here. 
            password_hash = password_context.hash(credentials.password)
        )
        return await self._add(new_doctor)