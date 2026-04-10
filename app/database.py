from app.core.database import async_session_maker
from app.core.database import engine
from app.core.database import get_db_session


async def get_async_uow_session():
    async for session in get_db_session():
        yield session
