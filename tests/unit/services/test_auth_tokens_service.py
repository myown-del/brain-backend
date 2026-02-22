from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from brain.application.abstractions.token_verifier import TokenInvalidError
from brain.application.interactors.auth.exceptions import JwtTokenInvalidException
from brain.application.services.auth_tokens import AuthTokensService
from brain.config.models import AuthenticationConfig
from brain.domain.entities.jwt import JwtAccessToken


@pytest.mark.asyncio
async def test_authorize_by_token_maps_invalid_token_error():
    jwt_service = Mock()
    jwt_service.decode_token.side_effect = TokenInvalidError()
    service = AuthTokensService(
        user_lookup_service=AsyncMock(),
        auth_config=AuthenticationConfig(admin_token="a", secret_key="b"),
        jwt_service=jwt_service,
        jwt_repo=AsyncMock(),
    )

    with pytest.raises(JwtTokenInvalidException):
        await service.authorize_by_token("bad")


@pytest.mark.asyncio
async def test_refresh_tokens_rejects_missing_record_even_with_valid_jwt():
    user_id = uuid4()
    jwt_service = Mock()
    jwt_service.decode_token.return_value = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    jwt_service.create_token.return_value = JwtAccessToken(
        access_token="access",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    jwt_repo = AsyncMock()
    jwt_repo.get_by_token.return_value = None
    service = AuthTokensService(
        user_lookup_service=AsyncMock(),
        auth_config=AuthenticationConfig(admin_token="a", secret_key="b"),
        jwt_service=jwt_service,
        jwt_repo=jwt_repo,
    )

    with pytest.raises(JwtTokenInvalidException):
        await service.refresh_tokens("refresh")
