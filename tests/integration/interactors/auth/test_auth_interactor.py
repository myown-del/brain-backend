from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from dishka import AsyncContainer

from brain.application.abstractions.repositories.jwt import IJwtRefreshTokensRepository
from brain.application.abstractions.token_verifier import TokenVerifier
from brain.application.interactors.auth.exceptions import (
    JwtTokenExpiredException,
    JwtTokenInvalidException,
)
from brain.application.interactors.auth.interactor import AuthInteractor
from brain.domain.entities.jwt import JwtRefreshToken
from brain.domain.entities.user import User


@pytest.mark.asyncio
async def test_login_stores_refresh_token(
    dishka_request: AsyncContainer,
    user: User,
):
    # setup: resolve interactor and repo
    auth_interactor = await dishka_request.get(AuthInteractor)
    jwt_repo = await dishka_request.get(IJwtRefreshTokensRepository)

    # action: log in and issue tokens
    tokens = await auth_interactor.login(user.telegram_id)

    # check: refresh token is persisted for the user
    stored = await jwt_repo.get_by_token(tokens.refresh_token)
    assert stored is not None
    assert stored.user_id == user.id
    assert stored.expires_at == tokens.refresh_expires_at

    await jwt_repo.delete_by_id(stored.id)


@pytest.mark.asyncio
async def test_refresh_tokens_rotates_refresh_token(
    dishka_request: AsyncContainer,
    user: User,
):
    # setup: resolve interactor and repo
    auth_interactor = await dishka_request.get(AuthInteractor)
    jwt_repo = await dishka_request.get(IJwtRefreshTokensRepository)

    # action: issue tokens and refresh them
    original_tokens = await auth_interactor.login(user.telegram_id)
    original_record = await jwt_repo.get_by_token(original_tokens.refresh_token)
    rotated_tokens = await auth_interactor.refresh_tokens(
        original_tokens.refresh_token,
    )

    # check: old token is removed and new token is stored
    assert original_record is not None
    assert await jwt_repo.get_by_id(original_record.id) is None
    rotated_record = await jwt_repo.get_by_token(rotated_tokens.refresh_token)
    assert rotated_record is not None
    assert rotated_record.id != original_record.id

    await jwt_repo.delete_by_id(rotated_record.id)


@pytest.mark.asyncio
async def test_refresh_tokens_rejects_missing_token(
    dishka_request: AsyncContainer,
    user: User,
):
    # setup: resolve interactor and token verifier
    auth_interactor = await dishka_request.get(AuthInteractor)
    token_verifier = await dishka_request.get(TokenVerifier)

    # action: create a valid token without persisting it
    token = token_verifier.create_token(payload={"user_id": user.id})

    # check: refreshing a missing token is rejected
    with pytest.raises(JwtTokenInvalidException):
        await auth_interactor.refresh_tokens(token.access_token)


@pytest.mark.asyncio
async def test_refresh_tokens_rejects_expired_record(
    dishka_request: AsyncContainer,
    user: User,
):
    # setup: resolve interactor, repo, and token verifier
    auth_interactor = await dishka_request.get(AuthInteractor)
    jwt_repo = await dishka_request.get(IJwtRefreshTokensRepository)
    token_verifier = await dishka_request.get(TokenVerifier)
    valid_jwt = token_verifier.create_token(
        payload={
            "user_id": user.id,
            "exp": datetime.utcnow() + timedelta(hours=1),
        },
    )
    expired_record = JwtRefreshToken(
        id=uuid4(),
        user_id=user.id,
        token=valid_jwt.access_token,
        expires_at=datetime.utcnow() - timedelta(seconds=1),
        created_at=datetime.utcnow(),
    )
    await jwt_repo.create(expired_record)

    # action: attempt to refresh token with expired record
    # check: expired record blocks refresh
    with pytest.raises(JwtTokenExpiredException):
        await auth_interactor.refresh_tokens(valid_jwt.access_token)

    # check: expired record can be removed cleanly
    await jwt_repo.delete_by_id(expired_record.id)


@pytest.mark.asyncio
async def test_authorize_by_token_returns_user(
    dishka_request: AsyncContainer,
    user: User,
):
    # setup: resolve interactor and token verifier
    auth_interactor = await dishka_request.get(AuthInteractor)
    token_verifier = await dishka_request.get(TokenVerifier)

    # action: authorize using a valid access token
    token = token_verifier.create_token(payload={"user_id": user.id})
    authorized_user = await auth_interactor.authorize_by_token(token.access_token)

    # check: authorized user matches token payload
    assert authorized_user.id == user.id
