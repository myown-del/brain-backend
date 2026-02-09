from uuid import UUID

import pytest
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from starlette import status

from brain.application.interactors.auth.interactor import AuthInteractor
from brain.config.models import Config
from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from brain.presentation.api.factory import create_bare_app
from tests.integration.api.conftest import ApiClientFactory


@pytest.mark.asyncio
async def test_api_key_can_manage_drafts_end_to_end(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
    user: User,
) -> None:
    # setup: create app, jwt token and api key
    config = await dishka_request.get(Config)
    auth_interactor = await dishka_request.get(AuthInteractor)
    tokens = await auth_interactor.login(telegram_id=user.telegram_id)
    app = create_bare_app(config=config.api)
    setup_dishka(container=dishka, app=app)

    async with api_client(app) as client:
        create_key_response = await client.request(
            method="POST",
            url="/api/api-keys/",
            headers={"Authorization": f"Bearer {tokens.access_token}"},
            json={"name": "drafts-key"},
        )
    assert create_key_response.status_code == status.HTTP_201_CREATED
    api_key = create_key_response.json()["key"]
    key_headers = {"X-API-Key": api_key}

    # action: create, read, search, update and delete draft with api key
    async with api_client(app) as client:
        create_response = await client.request(
            method="POST",
            url="/api/drafts",
            headers=key_headers,
            json={"text": "Draft from key #key"},
        )
    assert create_response.status_code == status.HTTP_201_CREATED
    draft_id = create_response.json()["id"]

    async with api_client(app) as client:
        get_response = await client.request(
            method="GET",
            url="/api/drafts",
            headers=key_headers,
        )
    assert get_response.status_code == status.HTTP_200_OK
    assert any(draft["id"] == draft_id for draft in get_response.json())

    async with api_client(app) as client:
        search_response = await client.request(
            method="POST",
            url="/api/drafts/search",
            headers=key_headers,
            json={"text_query": "from key"},
        )
    assert search_response.status_code == status.HTTP_200_OK
    assert [draft["id"] for draft in search_response.json()] == [draft_id]

    async with api_client(app) as client:
        update_response = await client.request(
            method="PATCH",
            url=f"/api/drafts/{draft_id}",
            headers=key_headers,
            json={"text": "Draft from key updated #key #updated"},
        )
    assert update_response.status_code == status.HTTP_200_OK
    assert sorted(update_response.json()["hashtags"]) == ["key", "updated"]

    async with api_client(app) as client:
        delete_response = await client.request(
            method="DELETE",
            url=f"/api/drafts/{draft_id}",
            headers=key_headers,
        )
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert await repo_hub.drafts.get_by_id(draft_id=UUID(draft_id)) is None


@pytest.mark.asyncio
async def test_invalid_api_key_falls_back_to_bearer_token_for_drafts(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client: ApiClientFactory,
    user: User,
) -> None:
    # setup: create app and valid bearer token
    config = await dishka_request.get(Config)
    auth_interactor = await dishka_request.get(AuthInteractor)
    tokens = await auth_interactor.login(telegram_id=user.telegram_id)
    app: FastAPI = create_bare_app(config=config.api)
    setup_dishka(container=dishka, app=app)

    # action: call drafts endpoint with invalid key and valid bearer token
    async with api_client(app) as client:
        response = await client.request(
            method="GET",
            url="/api/drafts",
            headers={
                "X-API-Key": "invalid-api-key",
                "Authorization": f"Bearer {tokens.access_token}",
            },
        )

    # check: bearer fallback authorizes request
    assert response.status_code == status.HTTP_200_OK
