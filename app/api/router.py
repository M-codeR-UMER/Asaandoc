from fastapi import APIRouter
from app.api.routers import doctor, patient

master_router = APIRouter()

master_router.include_router(doctor.router)
master_router.include_router(patient.router)