import os

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio(loop_scope="session")
async def test_import_todos_success(ac: AsyncClient):
    title = "Задача"
    details = "Описание задачи"
    tag = "Планы"
    created_at = "2023-10-01T00:00:00Z"
    source = "Созданная"

    data = {
        "title": title,
        "details": details,
        "tag": tag,
        "created_at": created_at,
        "completed_at": None,
        "source": source
    }

    if not os.path.exists("data"):
        os.mkdir("data")

    await ac.post("/todo/add/", data=data)
    await ac.post("/todo/export/")
    file_path = "data/todos.xlsx"

    with open(file_path, "rb") as file:
        files = {"file": ("todos.xlsx", file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = await ac.post("/todo/import", files=files)

    assert response.status_code == 303
    assert response.headers["location"] == "/todo/home"

    response = await ac.get("/todo/list/", params={
        "limit": 10,
        "skip": 0,
    })

    assert response.status_code == 200
    response_text = response.text

    assert title in response_text
    assert details in response_text
    assert tag in response_text
