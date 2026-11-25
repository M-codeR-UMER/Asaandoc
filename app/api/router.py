from fastapi import APIRouter

from app.api.routers import auth, doctor, patient

master_router = APIRouter()

master_router.include_router(auth.router)
master_router.include_router(doctor.router)
master_router.include_router(patient.router)
