from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import UserDB


class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, username: str) -> UserDB | None:
        result = await self.session.execute(select(UserDB).where(UserDB.name == username))
        return result.scalars().one_or_none()

    async def add_user(self, user: UserDB) -> UserDB:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def set_disabled(self, username: str, value: bool) -> None:
        await self.session.execute(update(UserDB).where(UserDB.name == username).values(disabled=value))

    async def delete_user(self, username: str) -> None:
        await self.session.execute(delete(UserDB).where(UserDB.name == username))

