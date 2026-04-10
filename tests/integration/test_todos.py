import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_add_todo_success(ac: AsyncClient):
    response = await ac.post(
        "/todo/add/",
        data={
            "title": "Задача",
            "details": "Описание задачи",
            "tag": "Планы",
            "source": "Созданная",
        },
    )

    assert response.status_code == 201
    assert response.json() == {"status": "success", "details": "Todo added"}


@pytest.mark.asyncio
async def test_get_todos_success(ac: AsyncClient):
    await ac.post(
        "/todo/add/",
        data={
            "title": "Найти книгу",
            "details": "Описание задачи",
            "tag": "Учёба",
            "source": "Созданная",
        },
    )

    response = await ac.get("/todo/list/", params={"limit": 10, "skip": 0})

    assert response.status_code == 200
    assert "Найти книгу" in response.text
    assert "Учёба" in response.text


@pytest.mark.asyncio
async def test_search_todos_by_query(ac: AsyncClient):
    await ac.post(
        "/todo/add/",
        data={
            "title": "Красная задача",
            "details": "Поиск по тексту",
            "tag": "Планы",
            "source": "Созданная",
        },
    )

    response = await ac.get("/todo/list/", params={"query": "Красная", "limit": 10, "skip": 0})

    assert response.status_code == 200
    assert "Красная задача" in response.text


@pytest.mark.asyncio
async def test_search_todos_by_attachment_content(ac: AsyncClient):
    await ac.post(
        "/todo/add/",
        data={
            "title": "Задача с файлом",
            "details": "Описание",
            "tag": "Личное",
            "source": "Созданная",
        },
    )

    response = await ac.put(
        "/todo/edit/1/",
        data={
            "title": "Задача с файлом",
            "details": "Описание",
            "completed": "false",
            "tag": "Личное",
            "created_at": "2024-10-01 10:00:00",
        },
        files={"attachment": ("note.txt", io.BytesIO("секретный контент".encode()), "text/plain")},
    )
    assert response.status_code == 200

    search_response = await ac.get("/todo/list/", params={"query": "контент", "limit": 10, "skip": 0})

    assert search_response.status_code == 200
    assert "Задача с файлом" in search_response.text


@pytest.mark.asyncio
async def test_delete_todo_success(ac: AsyncClient):
    await ac.post(
        "/todo/add/",
        data={
            "title": "Удалить меня",
            "details": "Описание задачи",
            "tag": "Планы",
            "source": "Созданная",
        },
    )

    response = await ac.delete("/todo/delete/1/")

    assert response.status_code == 200
    assert response.json()["details"] == "Todo deleted"
