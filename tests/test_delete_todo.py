import pytest
from httpx import AsyncClient


@pytest.mark.asyncio(loop_scope="session")
async def test_todo_delete_success(ac: AsyncClient):
    data = {
        "title": "Задача",
        "details": "Описание задачи",
        "tag": "Планы",
        "created_at": "2023-10-01T00:00:00Z",
        "completed_at": None,
        "source": "Созданная"
    }

    await ac.post("/todo/add/", data=data)
    response = await ac.delete("/todo/delete/1/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "details": "Todo deleted",
        "limit": 10,
        "skip": 0
    }


@pytest.mark.asyncio(loop_scope="session")
async def test_todo_delete_fail(ac: AsyncClient):
    response = await ac.delete("/todo/delete/1/")

    assert response.status_code == 404


@pytest.mark.asyncio(loop_scope="session")
async def test_all_todo_delete_success(ac: AsyncClient):
    data = {
        "title": "Задача",
        "details": "Описание задачи",
        "tag": "Планы",
        "created_at": "2023-10-01T00:00:00Z",
        "completed_at": None,
        "source": "Созданная"
    }

    await ac.post("/todo/add/", data=data)
    response = await ac.delete("/todo/delete/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "details": "Todos deleted",
        "limit": 10,
        "skip": 0
    }


@pytest.mark.asyncio(loop_scope="session")
async def test_all_todo_delete_fail(ac: AsyncClient):
    response = await ac.delete("/todo/delete/?start=10")

    assert response.status_code == 400