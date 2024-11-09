"""Database for todo
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models import Base

DB_PATH = "data"
DB_URL = f"sqlite+aiosqlite:///{DB_PATH}/db.sqlite"

engine = create_async_engine(DB_URL, connect_args={"check_same_thread": False})
# for logging all SQL-queries
#ENGINE = create_engine(DB_URL, connect_args={"check_same_thread": False}, echo=True)
async_session_maker = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def init_db():
    """Init database, create all models as tables
    """
    if not os.path.exists(DB_PATH):
        os.mkdir(DB_PATH)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_async_session():
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as exp:
            await session.rollback()
            raise exp

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
