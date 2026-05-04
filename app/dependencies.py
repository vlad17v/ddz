from typing import Annotated

from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.repositories.auth_repository import AuthRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.todo_repository import TodoRepository
from app.repositories.todo_search_repository import TodoSearchRepository
from app.services.auth_service import AuthService
from app.services.flower_service import FlowerService
from app.services.tag_service import TagService
from app.services.todo_service import TodoService
from app.utils.auth import OAuth2PasswordBearerWithCookie

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/auth/token")


async def get_todo_repository(session: AsyncSession = Depends(get_db_session)) -> TodoRepository:
    return TodoRepository(session)


async def get_auth_repository(session: AsyncSession = Depends(get_db_session)) -> AuthRepository:
    return AuthRepository(session)


async def get_tag_repository(session: AsyncSession = Depends(get_db_session)) -> TagRepository:
    return TagRepository(session)


async def get_search_repository(request: Request) -> TodoSearchRepository:
    return TodoSearchRepository(request.app.state.es_client)


async def get_todo_service(
    todo_repo: TodoRepository = Depends(get_todo_repository),
    search_repo: TodoSearchRepository = Depends(get_search_repository),
    tag_repo: TagRepository = Depends(get_tag_repository),
) -> TodoService:
    return TodoService(todo_repo, search_repo, tag_repo)


async def get_auth_service(auth_repo: AuthRepository = Depends(get_auth_repository)) -> AuthService:
    return AuthService(auth_repo)


async def get_tag_service(
    tag_repo: TagRepository = Depends(get_tag_repository),
    search_repo: TodoSearchRepository = Depends(get_search_repository),
) -> TagService:
    return TagService(tag_repo, search_repo)


async def get_flower_service() -> FlowerService:
    return FlowerService()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.get_current_user(token)


async def get_current_active_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: AuthService = Depends(get_auth_service),
):
    user = await auth_service.get_current_active_user(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    return user

