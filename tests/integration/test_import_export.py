import os

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_export_and_import_todos(ac: AsyncClient):
    await ac.post(
        "/todo/add/",
        data={
            "title": "Экспортируемая задача",
            "details": "Описание задачи",
            "tag": "Планы",
            "source": "Созданная",
        },
    )

    export_response = await ac.post("/todo/export/")
    assert export_response.status_code == 200

    file_path = "data/todos.xlsx"
    assert os.path.exists(file_path)

    with open(file_path, "rb") as file:
        import_response = await ac.post(
            "/todo/import/",
            files={"file": ("todos.xlsx", file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )

    assert import_response.status_code == 303
    assert import_response.headers["location"] == "/todo/home"


@pytest.mark.asyncio
async def test_import_log_page(ac: AsyncClient):
    response = await ac.get("/todo/import-log/")
    assert response.status_code == 200
