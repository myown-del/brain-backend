from unittest.mock import AsyncMock

import pytest

from brain.application.interactors.auth.exceptions import ApiKeyInvalidException, AuthorizationHeaderRequiredException
from brain.application.interactors.auth.request_authorization import RequestAuthorizationInteractor


@pytest.mark.asyncio
async def test_authorize_prefers_api_key_when_valid():
    auth_tokens = AsyncMock()
    api_keys = AsyncMock()
    user = object()
    api_keys.authorize.return_value = user
    interactor = RequestAuthorizationInteractor(auth_tokens, api_keys)

    result = await interactor.authorize("Bearer token", "api-key")

    assert result is user
    auth_tokens.authorize_by_token.assert_not_called()


@pytest.mark.asyncio
async def test_authorize_fallbacks_to_bearer_when_api_key_invalid():
    auth_tokens = AsyncMock()
    api_keys = AsyncMock()
    api_keys.authorize.side_effect = ApiKeyInvalidException()
    user = object()
    auth_tokens.authorize_by_token.return_value = user
    interactor = RequestAuthorizationInteractor(auth_tokens, api_keys)

    result = await interactor.authorize("Bearer access", "bad-key")

    assert result is user
    auth_tokens.authorize_by_token.assert_called_once_with("access")


@pytest.mark.asyncio
async def test_authorize_raises_api_key_invalid_when_no_bearer_fallback():
    auth_tokens = AsyncMock()
    api_keys = AsyncMock()
    api_keys.authorize.side_effect = ApiKeyInvalidException()
    interactor = RequestAuthorizationInteractor(auth_tokens, api_keys)

    with pytest.raises(ApiKeyInvalidException):
        await interactor.authorize(None, "bad-key")


@pytest.mark.asyncio
async def test_authorize_requires_bearer_when_no_api_key():
    interactor = RequestAuthorizationInteractor(AsyncMock(), AsyncMock())

    with pytest.raises(AuthorizationHeaderRequiredException):
        await interactor.authorize(None, None)
