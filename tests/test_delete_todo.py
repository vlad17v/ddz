import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker


from ..app.database import get_async_session
from app.repository import TodoRepository  # Adjust import based on your app structure
from app.models import Todo


# Create a new FastAPI app for testing
@pytest.fixture(scope="module")
def test_app():
    app.dependency_overrides[get_async_session] = override_get_async_session  # Override the dependency to use test DB
    yield app


@pytest.fixture(scope="module")
def client(test_app):
    return TestClient(test_app)


@pytest.fixture(scope="module")
async def db_session():
    # Set up your test database session here
    engine = create_async_engine("sqlite+aiosqlite:///./test.db", echo=True)
    async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

    # Create a test todo repository
    async with async_session() as session:
        yield session


@pytest.fixture
async def override_get_async_session(db_session):
    async def _get_async_session():
        yield db_session

    return _get_async_session


@pytest.mark.asyncio
async def test_delete_todo_success(client, db_session):
    # Create a todo for testing
    todo_repo = TodoRepository(db_session)
    todo = Todo(title="Test Todo", done=False)  # Adjust based on your TodoModel
    db_session.add(todo)
    await db_session.commit()
    await db_session.refresh(todo)

    # Call the delete endpoint
    response = client.delete(f"/delete/{todo.id}/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "status": "success",
        "details": "Todo deleted"
    }

    # Verify the todo is deleted
    deleted_todo = await todo_repo.get_todo(todo.id)
    assert deleted_todo is None


@pytest.mark.asyncio
async def test_delete_todo_not_found(client):
    # Attempt to delete a todo that doesn't exist
    response = client.delete("/delete/9999/")  # Assuming 9999 is a non-existent todo ID

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Not found todo by this id: 9999"
    }
