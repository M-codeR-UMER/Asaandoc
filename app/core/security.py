from fastapi.security import OAuth2PasswordBearer

oauth2_scheme_patient = OAuth2PasswordBearer(tokenUrl="/patient/token")
oauth2_scheme_doctor = OAuth2PasswordBearer(tokenUrl="/doctor/token")