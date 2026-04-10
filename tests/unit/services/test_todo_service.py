from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.models.db import TodoDB
from app.models.schemas import Tags
from app.services.todo_service import TodoService


@pytest.mark.asyncio
async def test_list_todos_uses_search_repository_when_filters_exist():
    repo = AsyncMock()
    repo.get_todos_by_ids.return_value = [TodoDB(id=1, title="Task", details="Details", tag="Планы", source="Созданная")]
    search_repo = AsyncMock()
    search_repo.search_todos.return_value = {"ids": [1], "total": 1}

    service = TodoService(repo, search_repo)
    todos, total = await service.list_todos(
        limit=10,
        skip=0,
        creation_date_start=datetime(2024, 1, 1),
        creation_date_end=None,
        tag=Tags.plans,
        query="task",
    )

    assert total == 1
    assert todos[0].title == "Task"
    search_repo.search_todos.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_todos_falls_back_to_database():
    repo = AsyncMock()
    repo.get_todos.return_value = [TodoDB(id=1, title="Task", details="Details", tag="Планы", source="Созданная")]
    repo.get_count_todos.return_value = 1
    search_repo = AsyncMock()
    search_repo.search_todos.return_value = None

    service = TodoService(repo, search_repo)
    todos, total = await service.list_todos(
        limit=10,
        skip=0,
        creation_date_start=None,
        creation_date_end=None,
        tag=None,
        query=None,
    )

    assert total == 1
    assert todos[0].title == "Task"
    repo.get_todos.assert_awaited_once()
