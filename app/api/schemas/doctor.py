from pydantic import BaseModel, EmailStr

from app.database.models import Gender, MaritalStatus


class BaseDoctor(BaseModel):
    name: str
    email: EmailStr


class DoctorCreate(BaseDoctor):
    password: str


# this will be shown to Doctor as an output of register route
class DoctorRead(BaseDoctor):
    # email, name will be shown.
    pass

# For the purpose of handling error
class DoctorForm(BaseModel):
    age: int | None
    gender: Gender | None
    marital_status: MaritalStatus | None
