import pytest
from httpx import AsyncClient

from app.uow import UnitOfWork


@pytest.mark.asyncio(loop_scope="session")
async def test_import_todos_success(authenticated_client: AsyncClient, uow_session: UnitOfWork):
    file_path = "data/test_import_success.xlsx"

    with open(file_path, "rb") as file:
        files = {"file": ("test_import_success.xlsx", file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = await authenticated_client.post("/todo/import", files=files)

    assert response.status_code == 303
    assert response.headers["location"] == "/todo/home"

    todos = await uow_session.todo.get_all_todos()
    todos = list(reversed(todos))

    assert todos[0].title == "Задача 1"
    assert todos[0].details == "Погулять с собакой"
    assert todos[0].tag == "Личное"
    assert todos[0].completed == False
    assert todos[0].source == "Импортированная"
    assert todos[0].image_path is None
    assert todos[0].image_hash is None

    assert todos[1].title == "Задача 2"
    assert todos[1].details == "Купить молоко"
    assert todos[1].tag == "Планы"
    assert todos[1].completed == False
    assert todos[1].source == "Импортированная"
    assert todos[1].image_path is None
    assert todos[1].image_hash is None

    assert todos[2].title == "Задача 3"
    assert todos[2].details == "Приготовить ужин"
    assert todos[2].tag == "Учеба"
    assert todos[2].completed == False
    assert todos[2].source == "Импортированная"
    assert todos[2].image_path is None
    assert todos[2].image_hash is None

@pytest.mark.asyncio(loop_scope="session")
async def test_import_todos_invalid_file(authenticated_client: AsyncClient):
    file_path = "data/test_import_invalid.xlsx"

    with open(file_path, "rb") as file:
        files = {"file": ("test_import_invalid.xlsx", file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = await authenticated_client.post("/todo/import", files=files)

    assert response.status_code == 303

@pytest.mark.asyncio(loop_scope="session")
async def test_import_todos_empty_file(authenticated_client: AsyncClient):
    file_path = "data/test_import_empty.xlsx"

    with open(file_path, "rb") as file:
        files = {"file": ("test_import_empty.xlsx", file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = await authenticated_client.post("/todo/import", files=files)

    assert response.status_code == 303