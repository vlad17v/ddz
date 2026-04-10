from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.models.db import UserDB
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_authenticate_success():
    repo = AsyncMock()
    repo.get_user.return_value = UserDB(name="user", password="pass", disabled=False)
    service = AuthService(repo)

    user = await service.authenticate("user", "pass")

    assert user.name == "user"
    repo.set_disabled.assert_awaited_once_with("user", False)


@pytest.mark.asyncio
async def test_register_duplicate_user():
    repo = AsyncMock()
    repo.get_user.return_value = UserDB(name="user", password="pass", disabled=False)
    service = AuthService(repo)

    with pytest.raises(HTTPException):
        await service.register("user", "pass")
