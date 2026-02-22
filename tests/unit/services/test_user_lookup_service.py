from uuid import uuid4
from unittest.mock import AsyncMock

import pytest

from brain.application.interactors.users.exceptions import UserNotFoundException
from brain.application.services.user_lookup import UserLookupService


@pytest.mark.asyncio
async def test_get_user_by_id_returns_user():
    repo = AsyncMock()
    user = object()
    repo.get_by_id.return_value = user
    service = UserLookupService(users_repo=repo)

    result = await service.get_user_by_id(uuid4())

    assert result is user


@pytest.mark.asyncio
async def test_get_user_by_telegram_id_raises_not_found():
    repo = AsyncMock()
    repo.get_by_telegram_id.return_value = None
    service = UserLookupService(users_repo=repo)

    with pytest.raises(UserNotFoundException):
        await service.get_user_by_telegram_id(123)
