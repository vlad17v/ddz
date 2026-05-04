from fastapi import HTTPException
from fastapi import status

from app.models.db import TagDB
from app.repositories.tag_repository import TagRepository
from app.repositories.todo_search_repository import TodoSearchRepository


class TagService:
    def __init__(self, tag_repo: TagRepository, search_repo: TodoSearchRepository):
        self.tag_repo = tag_repo
        self.search_repo = search_repo

    async def get_all_tags(self) -> list[TagDB]:
        return await self.tag_repo.get_all_tags()

    async def create_tag(self, name: str) -> TagDB:
        name = name.strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tag name cannot be empty")
        existing = await self.tag_repo.get_tag_by_name(name)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag already exists")
        tag = await self.tag_repo.add_tag(name)
        await self.tag_repo.commit()
        return tag

    async def delete_tag(self, tag_id: int) -> None:
        tag = await self.tag_repo.get_tag_by_id(tag_id)
        if not tag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
        await self.tag_repo.delete_tag(tag_id)
        await self.tag_repo.commit()

    async def suggest_tags(self, prefix: str, size: int = 10) -> list[str]:
        # задача 3: сначала ES, fallback на DB
        suggestions = await self.search_repo.suggest_tags(prefix, size)
        if suggestions is not None:
            return suggestions
        return await self.tag_repo.search_by_prefix(prefix, size)
