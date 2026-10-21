from contextlib import asynccontextmanager

from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference

from app.api.router import master_router
from app.database.session import create_db_tables

@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    await create_db_tables()
    yield

# This is markdown description for the Api documentation.Remember this is markdown description.
description = """

Doctors and Patient Telehealth Management System for Doctors and Patients.

### Patient
- Register a patient
- Login a patient
- Logout a patient

### Doctor
- Register a doctor
- Login a doctor
- Logout a doctor

"""

app = FastAPI(
    title="Asaandoc",
    # Server start and stoop listener
    lifespan=lifespan_handler,
    description=description, # Markdown description is reflected here.
    docs_url="/swagger", # Changing /docs to /swagger
    version="0.1.0",
    contact={
        "name": "Muhammad Alber",
        "email": "albermalik111@gmail.com",
        "url": "https://linkedin.com/in/muhammad-alber/"
    }
)

# Add all endpoints | routers
app.include_router(master_router)

# Scaler APi documentation
@app.get("/scalar", include_in_schema=False)
async def get_scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="AsaanDoc Documentation",
    )
