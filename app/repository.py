from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import insert
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import update
from sqlalchemy import delete

from app.models import Todo


class TodoRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_count_todos(self):
        count_todo = await self._session.execute(
            select(func.count()).select_from(Todo)
        )
        data = count_todo.scalar()
        return data

    async def get_todos(self, limit: int, skip: int):
        find_todos = await self._session.execute(
            select(Todo).order_by(desc(Todo.id)).offset(skip * limit).limit(limit)
        )
        data = find_todos.scalars().all()
        return data

    async def add_todo(self, data: dict):
        await self._session.execute(
            insert(Todo).values(**data)
        )

    async def get_todo(self, todo_id: int):
        find_todo = await self._session.execute(
            select(Todo).where(Todo.id == todo_id)
        )
        data = find_todo.scalars().one_or_none()
        return data

    async def update_todo(self, todo_id: int, data: dict):
        await self._session.execute(
            update(Todo).where(Todo.id == todo_id).values(**data)
        )

    async def delete_todo(self, todo_id: int):
        await self._session.execute(
            delete(Todo).where(Todo.id == todo_id)
        )
