from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import TagDB


class TagRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_tags(self) -> list[TagDB]:
        result = await self.session.execute(select(TagDB).order_by(TagDB.name))
        return list(result.scalars().all())

    async def get_tag_by_id(self, tag_id: int) -> TagDB | None:
        result = await self.session.execute(select(TagDB).where(TagDB.id == tag_id))
        return result.scalars().one_or_none()

    async def get_tag_by_name(self, name: str) -> TagDB | None:
        result = await self.session.execute(select(TagDB).where(TagDB.name == name))
        return result.scalars().one_or_none()

    async def get_or_create_tags(self, names: list[str]) -> list[TagDB]:
        result: list[TagDB] = []

        unique_names = list(dict.fromkeys(names))

        for name in unique_names:
            tag = await self.get_tag_by_name(name)
            if not tag:
                tag = TagDB(name=name)
                self.session.add(tag)
                await self.session.flush()
                await self.session.refresh(tag)
            result.append(tag)

        seen_ids = set()
        unique_result = []
        for tag in result:
            if tag.id not in seen_ids:
                unique_result.append(tag)
                seen_ids.add(tag.id)

        return unique_result

    async def add_tag(self, name: str) -> TagDB:
        tag = TagDB(name=name)
        self.session.add(tag)
        await self.session.flush()
        await self.session.refresh(tag)
        return tag

    async def delete_tag(self, tag_id: int) -> None:
        await self.session.execute(delete(TagDB).where(TagDB.id == tag_id))

    async def search_by_prefix(self, prefix: str, limit: int = 10) -> list[str]:
        query = (
            select(TagDB.name)
            .where(TagDB.name.ilike(f"{prefix}%"))
            .order_by(TagDB.name)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def commit(self) -> None:
        await self.session.commit()
