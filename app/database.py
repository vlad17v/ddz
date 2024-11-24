"""Database for todo
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models import Base

import os

DB_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:123@localhost:5432/db")

engine = create_async_engine(DB_URL)
# for logging all SQL-queries
# ENGINE = create_engine(DB_URL, connect_args={"check_same_thread": False}, echo=True)
async_session_maker = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def init_db():
    """Init database, create all models as tables
    """

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
