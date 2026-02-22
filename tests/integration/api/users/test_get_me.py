from contextlib import asynccontextmanager
from datetime import datetime
from collections.abc import AsyncIterator, Callable
from uuid import uuid4

import pytest
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from starlette import status

from brain.config.models import Config
from brain.domain.entities.s3_file import S3File
from brain.domain.entities.user import User
from brain.application.interactors.auth.interactor import AuthInteractor
from brain.infrastructure.db.repositories.hub import RepositoryHub
from brain.presentation.api.factory import create_bare_app

ApiClientFactory = Callable[[FastAPI], AsyncIterator[AsyncClient]]


def _parse_api_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


@pytest.fixture
def api_client() -> ApiClientFactory:
    @asynccontextmanager
    async def _client(app: FastAPI) -> AsyncIterator[AsyncClient]:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    return _client


@pytest.mark.asyncio
async def test_get_me_returns_user_info(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    repo_hub: RepositoryHub,
    api_client,
):
    # setup: create user and issue access token
    created_at = datetime(
        year=2024,
        month=1,
        day=2,
        hour=3,
        minute=4,
        second=5,
    )
    user = User(
        id=uuid4(),
        telegram_id=123456,
        username="api_user",
        first_name="Api",
        last_name="User",
        created_at=created_at,
        updated_at=created_at,
    )
    await repo_hub.users.create(entity=user)

    # setup: attach profile picture
    config = await dishka_request.get(Config)
    profile_picture = S3File(
        id=uuid4(),
        name="profile.jpg",
        path=f"avatars/{user.id}/profile.jpg",
        content_type="image/jpeg",
    )
    await repo_hub.s3_files.create(entity=profile_picture)
    user.profile_picture_file_id = profile_picture.id
    await repo_hub.users.update(entity=user)

    stored_user = await repo_hub.users.get_by_id(entity_id=user.id)
    auth_interactor = await dishka_request.get(AuthInteractor)
    tokens = await auth_interactor.login(telegram_id=user.telegram_id)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)

    # action: request current user endpoint
    async with api_client(app) as client:
        response = await client.request(
            method="GET",
            url="/api/users/me",
            headers={"Authorization": f"Bearer {tokens.access_token}"},
        )

    # check: response matches stored user fields
    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert stored_user is not None
    assert payload["id"] == str(stored_user.id)
    assert payload["telegram_id"] == stored_user.telegram_id
    assert payload["username"] == stored_user.username
    assert payload["first_name"] == stored_user.first_name
    assert payload["last_name"] == stored_user.last_name
    assert _parse_api_datetime(payload["created_at"]) == stored_user.created_at
    assert _parse_api_datetime(payload["updated_at"]) == stored_user.updated_at

    assert payload["profile_picture"] is not None
    assert payload["profile_picture"]["id"] == str(profile_picture.id)
    assert payload["profile_picture"]["name"] == profile_picture.name
    assert payload["profile_picture"]["path"] == profile_picture.path
    assert payload["profile_picture"]["content_type"] == "image/jpeg"
    assert (
        payload["profile_picture"]["url"]
        == f"{config.s3.external_host}/{profile_picture.path}"
    )


@pytest.mark.asyncio
async def test_get_me_rejects_invalid_token(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
):
    # setup: create app with full container
    config = await dishka_request.get(Config)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)

    # action: request with invalid token
    async with api_client(app) as client:
        response = await client.request(
            method="GET",
            url="/api/users/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

    # check: unauthorized response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
