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


@pytest.mark.asyncio
async def test_top_words_page_shows_aggregated_words(ac: AsyncClient):
    await ac.post(
        "/todo/add/",
        data={
            "title": "Красная папка",
            "details": "Красная задача",
            "tag": "Планы",
            "source": "Созданная",
        },
    )
    await ac.post(
        "/todo/add/",
        data={
            "title": "Синяя задача",
            "details": "Красная заметка",
            "tag": "Личное",
            "source": "Созданная",
        },
    )

    response = await ac.get("/todo/top-words/")

    assert response.status_code == 200
    assert "Топ-10 популярных слов" in response.text
    assert "красная" in response.text
    assert ">3<" in response.text


@pytest.mark.asyncio
async def test_search_uses_sanitized_text_in_search_index(ac: AsyncClient):
    await ac.post(
        "/todo/add/",
        data={
            "title": "Секретная задача",
            "details": "Совершенно секретно и конфиденциально",
            "tag": "Планы",
            "source": "Созданная",
        },
    )

    response_secret = await ac.get("/todo/list/", params={"query": "секретно", "limit": 10, "skip": 0})
    response_safe = await ac.get("/todo/list/", params={"query": "неинтересно", "limit": 10, "skip": 0})

    assert response_secret.status_code == 200
    assert "Секретная задача" not in response_secret.text
    assert response_safe.status_code == 200
    assert "Секретная задача" in response_safe.text
