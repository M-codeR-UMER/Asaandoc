from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from app.config import db_settings

# Creating a database engine to connect to database 
engine = create_async_engine(
    url= db_settings.POSTGRES_URL,
    echo = True 
)

async def create_db_tables():
    async with engine.begin() as connection:
        from .models import Patient, Doctor # noqa: F401
        await connection.run_sync(SQLModel.metadata.create_all)

# Sessiions to intreact with database
async def get_session():
    async_session = sessionmaker(
        class_=AsyncSession,
        bind= engine,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session