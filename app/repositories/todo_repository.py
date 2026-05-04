from datetime import datetime

from sqlalchemy import and_
from sqlalchemy import case
from sqlalchemy import delete
from sqlalchemy import desc
from sqlalchemy import distinct
from sqlalchemy import func
from sqlalchemy import insert
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import TagDB
from app.models.db import TodoDB
from app.models.db import todo_tags


class TodoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def flush(self) -> None:
        await self.session.flush()

    async def refresh(self, todo: TodoDB) -> None:
        await self.session.refresh(todo)

    def _apply_filters(
        self,
        query,
        creation_date_start: datetime | None,
        creation_date_end: datetime | None,
        tag: str | None,
        text_query: str | None,
    ):
        if creation_date_start:
            query = query.where(TodoDB.created_at >= creation_date_start)
        if creation_date_end:
            query = query.where(TodoDB.created_at <= creation_date_end)
        if tag:
            tagged_ids = (
                select(TodoDB.id).join(TodoDB.tags).where(TagDB.name == tag).subquery()
            )
            query = query.where(TodoDB.id.in_(tagged_ids))
        if text_query:
            pattern = f"%{text_query}%"
            query = query.where(or_(TodoDB.title.ilike(pattern), TodoDB.details.ilike(pattern)))
        return query

    async def get_count_todos(
        self,
        creation_date_start: datetime | None = None,
        creation_date_end: datetime | None = None,
        tag: str | None = None,
        text_query: str | None = None,
    ) -> int:
        query = select(func.count()).select_from(TodoDB)
        query = self._apply_filters(query, creation_date_start, creation_date_end, tag, text_query)
        result = await self.session.execute(query)
        return int(result.scalar() or 0)

    async def get_todos(
        self,
        limit: int,
        skip: int,
        creation_date_start: datetime | None = None,
        creation_date_end: datetime | None = None,
        tag: str | None = None,
        text_query: str | None = None,
    ) -> list[TodoDB]:
        query = select(TodoDB).order_by(desc(TodoDB.id)).offset(skip * limit).limit(limit)
        query = self._apply_filters(query, creation_date_start, creation_date_end, tag, text_query)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_todos_by_ids(self, ids: list[int]) -> list[TodoDB]:
        if not ids:
            return []
        order = case({todo_id: index for index, todo_id in enumerate(ids)}, value=TodoDB.id)
        result = await self.session.execute(select(TodoDB).where(TodoDB.id.in_(ids)).order_by(order))
        return list(result.scalars().all())

    async def get_all_todos(self) -> list[TodoDB]:
        result = await self.session.execute(select(TodoDB).order_by(desc(TodoDB.id)))
        return list(result.scalars().all())

    async def get_todo(self, todo_id: int) -> TodoDB | None:
        result = await self.session.execute(select(TodoDB).where(TodoDB.id == todo_id))
        return result.scalars().one_or_none()

    async def add_todo(self, todo: TodoDB) -> TodoDB:
        self.session.add(todo)
        await self.session.flush()
        await self.session.refresh(todo)
        return todo

    async def update_todo(self, todo_id: int, data: dict) -> None:
        await self.session.execute(update(TodoDB).where(TodoDB.id == todo_id).values(**data))

    async def set_todo_tags(self, todo_id: int, tags: list[TagDB]) -> None:
        await self.session.execute(delete(todo_tags).where(todo_tags.c.todo_id == todo_id))
        if tags:
            await self.session.execute(
                insert(todo_tags),
                [{"todo_id": todo_id, "tag_id": tag.id} for tag in tags],
            )

    async def delete_todo(self, todo_id: int) -> None:
        await self.session.execute(delete(TodoDB).where(TodoDB.id == todo_id))

    async def delete_todos(self, ids: list[int]) -> None:
        if ids:
            await self.session.execute(delete(TodoDB).where(TodoDB.id.in_(ids)))

    async def delete_all_todos(self) -> None:
        await self.session.execute(delete(TodoDB))

    async def get_all_image_paths(self) -> list[str]:
        result = await self.session.execute(select(distinct(TodoDB.image_path)).where(TodoDB.image_path.is_not(None)))
        return list(result.scalars().all())

    async def find_duplicate_image_path(self, image_hash: str) -> str | None:
        result = await self.session.execute(select(TodoDB).where(TodoDB.image_hash == image_hash))
        todo = result.scalars().first()
        return todo.image_path if todo else None

    async def get_other_todo_by_image_path(self, image_path: str | None, todo_id: int) -> TodoDB | None:
        if not image_path:
            return None
        result = await self.session.execute(
            select(TodoDB).where(and_(TodoDB.image_path == image_path, TodoDB.id != todo_id))
        )
        return result.scalars().first()

    async def get_todo_by_attachment_path(self, attachment_path: str | None) -> TodoDB | None:
        if not attachment_path:
            return None
        result = await self.session.execute(select(TodoDB).where(TodoDB.attachment_path == attachment_path))
        return result.scalars().first()

