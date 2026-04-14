import re
from collections import Counter
from collections.abc import AsyncGenerator
from datetime import datetime

import pytest
from httpx import ASGITransport
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.database import get_db_session
from app.dependencies import get_search_repository
from app.main import app
from app.models.db import Base


class FakeSearchRepository:
    def __init__(self):
        self.documents: dict[int, dict] = {}
        self.word_pattern = re.compile(r"[a-zA-Zа-яА-ЯёЁ-]+")

    @staticmethod
    def _normalize_datetime(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value
        return value.replace(tzinfo=None)

    async def index_todo(self, todo_id: int, document: dict) -> bool:
        self.documents[todo_id] = document
        return True

    async def delete_todo(self, todo_id: int) -> bool:
        self.documents.pop(todo_id, None)
        return True

    async def search_todos(
        self,
        *,
        query: str | None,
        tag: str | None,
        creation_date_start: datetime | None,
        creation_date_end: datetime | None,
        skip: int,
        limit: int,
    ) -> dict:
        items = list(self.documents.values())

        if query:
            lowered = query.lower()
            items = [
                item
                for item in items
                if lowered in (item.get("title") or "").lower()
                or lowered in (item.get("details") or "").lower()
                or lowered in (item.get("tag") or "").lower()
                or lowered in (item.get("attachment_text") or "").lower()
            ]

        if tag:
            items = [item for item in items if item.get("tag") == tag]

        if creation_date_start:
            items = [
                item
                for item in items
                if item.get("created_at")
                and self._normalize_datetime(datetime.fromisoformat(item["created_at"]))
                >= self._normalize_datetime(creation_date_start)
            ]

        if creation_date_end:
            items = [
                item
                for item in items
                if item.get("created_at")
                and self._normalize_datetime(datetime.fromisoformat(item["created_at"]))
                <= self._normalize_datetime(creation_date_end)
            ]

        items.sort(key=lambda item: (item.get("created_at") or "", item["id"]), reverse=True)
        total = len(items)
        page = items[skip * limit : skip * limit + limit]
        return {"ids": [item["id"] for item in page], "total": total}

    async def analyze_texts(self, texts: list[str]) -> list[str]:
        counts = Counter()
        for text in texts:
            for word in self.word_pattern.findall((text or "").lower()):
                cleaned = word.strip("-")
                if len(cleaned) >= 3:
                    counts[cleaned] += 1
        return list(counts.elements())


TEST_DB_URL = "sqlite+aiosqlite:///./data/test.db"
engine_test = create_async_engine(TEST_DB_URL, future=True)
session_maker = async_sessionmaker(engine_test, expire_on_commit=False, class_=AsyncSession)

fake_search = FakeSearchRepository()


async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def override_get_search_repository():
    return fake_search


app.dependency_overrides[get_db_session] = override_get_db_session
app.dependency_overrides[get_search_repository] = override_get_search_repository


@pytest.fixture(autouse=True, scope="session")
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
async def clear_search():
    fake_search.documents.clear()
    yield
    fake_search.documents.clear()


@pytest.fixture(autouse=True)
async def clear_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/auth/register", data={"username": "username", "password": "password"})
        await client.post("/auth/token", data={"username": "username", "password": "password"})
        client.cookies.set("access_token", "Bearer username")
        yield client
