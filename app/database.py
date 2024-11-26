"""Database for todo
"""
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import DB_HOST
from app.config import DB_PORT
from app.config import DB_USER
from app.config import DB_NAME
from app.config import DB_PASS
from app.uow import UnitOfWork


DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
uow = UnitOfWork(async_session_maker)

async def get_async_uow_session() -> UnitOfWork:
    async with uow.start() as uow_session:
        yield uow_session
