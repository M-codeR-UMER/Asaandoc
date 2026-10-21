from pydantic import BaseModel, EmailStr

from app.database.models import Gender, MaritalStatus


class BasePatient(BaseModel):
    name: str
    email: EmailStr


class PatientCreate(BasePatient):
    password: str


# this will be shown to patient as an output of login route
class PatientRead(BasePatient):
    # email, name will be shown.
    pass

# For the purpose of handling error
class Patientform(BaseModel):
    age: int | None
    gender: Gender | None
    marital_status: MaritalStatus | None
