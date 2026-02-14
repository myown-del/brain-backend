import asyncio
from datetime import datetime, timezone

import pytest
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from starlette import status

from brain.config.models import Config
from brain.domain.entities.user import User
from brain.presentation.api.factory import create_bare_app


@pytest.mark.asyncio
async def test_fake_auth_creates_tokens(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
    user: User,
):
    # setup: configure admin token and app
    config = await dishka_request.get(Config)
    original_admin_token = config.auth.admin_token
    config.auth.admin_token = "test-admin-token"
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)

    try:
        # action: request tokens for existing user
        async with api_client(app) as client:
            response = await client.request(
                method="POST",
                url="/api/auth/fake",
                json={
                    "user_telegram_id": user.telegram_id,
                    "admin_token": "test-admin-token",
                },
            )

        # check: tokens are returned with timestamps
        assert response.status_code == status.HTTP_200_OK
        payload = response.json()
        assert payload["access_token"]
        assert payload["refresh_token"]
        assert datetime.fromisoformat(payload["expires_at"]).tzinfo == timezone.utc
        assert datetime.fromisoformat(payload["refresh_expires_at"]).tzinfo == timezone.utc
    finally:
        config.auth.admin_token = original_admin_token


@pytest.mark.asyncio
async def test_refresh_token_rotates_tokens(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
    user: User,
):
    # setup: configure admin token and app
    config = await dishka_request.get(Config)
    original_admin_token = config.auth.admin_token
    config.auth.admin_token = "test-admin-token"
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)

    try:
        # setup: issue initial tokens
        async with api_client(app) as client:
            initial_response = await client.request(
                method="POST",
                url="/api/auth/fake",
                json={
                    "user_telegram_id": user.telegram_id,
                    "admin_token": "test-admin-token",
                },
            )
        initial_payload = initial_response.json()
        refresh_token = initial_payload["refresh_token"]

        # action: wait for a new token timestamp and refresh tokens
        await asyncio.sleep(2)
        async with api_client(app) as client:
            refresh_response = await client.request(
                method="POST",
                url="/api/auth/tokens/refresh",
                json={"refresh_token": refresh_token},
            )

        # check: new tokens are returned and rotated
        assert refresh_response.status_code == status.HTTP_200_OK
        refreshed_payload = refresh_response.json()
        assert refreshed_payload["access_token"] != initial_payload["access_token"]
        assert refreshed_payload["refresh_token"] != refresh_token
    finally:
        config.auth.admin_token = original_admin_token


@pytest.mark.asyncio
async def test_refresh_token_expiration_returns_unauthorized(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
    user: User,
):
    # setup: configure admin token, short refresh lifetime, and app
    config = await dishka_request.get(Config)
    original_admin_token = config.auth.admin_token
    original_refresh_lifetime = config.auth.refresh_token_lifetime
    config.auth.admin_token = "test-admin-token"
    config.auth.refresh_token_lifetime = 1
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)

    try:
        # setup: issue initial tokens
        async with api_client(app) as client:
            initial_response = await client.request(
                method="POST",
                url="/api/auth/fake",
                json={
                    "user_telegram_id": user.telegram_id,
                    "admin_token": "test-admin-token",
                },
            )
        refresh_token = initial_response.json()["refresh_token"]

        # action: wait for refresh token to expire and refresh
        await asyncio.sleep(2)
        async with api_client(app) as client:
            refresh_response = await client.request(
                method="POST",
                url="/api/auth/tokens/refresh",
                json={"refresh_token": refresh_token},
            )

        # check: expired token is rejected
        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED
        assert refresh_response.json()["detail"] == "Token expired"
    finally:
        config.auth.admin_token = original_admin_token
        config.auth.refresh_token_lifetime = original_refresh_lifetime
