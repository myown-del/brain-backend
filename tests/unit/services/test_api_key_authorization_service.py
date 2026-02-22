from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from brain.application.interactors.auth.exceptions import ApiKeyInvalidException
from brain.application.services.api_key_authorization import ApiKeyAuthorizationService


@pytest.mark.asyncio
async def test_authorize_returns_user_for_valid_api_key():
    user_id = uuid4()
    repo = AsyncMock()
    repo.get_by_hash.return_value = SimpleNamespace(user_id=user_id)
    api_key_service = Mock()
    api_key_service.hash_key.return_value = "hash"
    user_lookup = AsyncMock()
    user = object()
    user_lookup.get_user_by_id.return_value = user

    service = ApiKeyAuthorizationService(
        api_keys_repo=repo,
        api_key_service=api_key_service,
        user_lookup_service=user_lookup,
    )

    result = await service.authorize("key")

    assert result is user
    api_key_service.hash_key.assert_called_once_with("key")


@pytest.mark.asyncio
async def test_authorize_raises_for_invalid_api_key():
    repo = AsyncMock()
    repo.get_by_hash.return_value = None
    api_key_service = Mock()
    api_key_service.hash_key.return_value = "hash"

    service = ApiKeyAuthorizationService(
        api_keys_repo=repo,
        api_key_service=api_key_service,
        user_lookup_service=AsyncMock(),
    )

    with pytest.raises(ApiKeyInvalidException):
        await service.authorize("key")
