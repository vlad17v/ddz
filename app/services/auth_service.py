from fastapi import status
from fastapi import HTTPException

from app.models.db import UserDB
from app.repositories.auth_repository import AuthRepository


class AuthService:
    def __init__(self, auth_repo: AuthRepository):
        self.auth_repo = auth_repo

    async def authenticate(self, username: str, password: str) -> UserDB:
        user = await self.auth_repo.get_user(username)
        if not user or user.password != password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect username or password",
            )
        await self.auth_repo.set_disabled(username, False)
        return user

    async def get_current_user(self, username: str) -> UserDB:
        user = await self.auth_repo.get_user(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    async def get_current_active_user(self, username: str) -> UserDB:
        user = await self.get_current_user(username)
        if user.disabled:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
        return user

    async def register(self, username: str, password: str) -> UserDB:
        existing_user = await self.auth_repo.get_user(username)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
        return await self.auth_repo.add_user(UserDB(name=username, password=password, disabled=False))

    async def logout(self, username: str) -> None:
        await self.auth_repo.set_disabled(username, True)

