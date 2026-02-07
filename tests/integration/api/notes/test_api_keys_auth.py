import pytest
from uuid import UUID
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from starlette import status

from brain.application.interactors.auth.interactor import AuthInteractor
from brain.config.models import Config
from brain.infrastructure.db.repositories.hub import RepositoryHub
from brain.presentation.api.factory import create_bare_app


@pytest.mark.asyncio
async def test_api_key_can_manage_notes_end_to_end(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    # setup: create app, issue jwt, and create api key
    config = await dishka_request.get(Config)
    auth_interactor = await dishka_request.get(AuthInteractor)
    tokens = await auth_interactor.login(user.telegram_id)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)

    async with api_client(app) as client:
        create_key_response = await client.request(
            method="POST",
            url="/api/api-keys/",
            headers={"Authorization": f"Bearer {tokens.access_token}"},
            json={"name": "notes-key"},
        )
    assert create_key_response.status_code == status.HTTP_201_CREATED
    api_key = create_key_response.json()["key"]
    key_headers = {"X-API-Key": api_key}

    # action: create, read, search, update, and delete note using api key
    async with api_client(app) as client:
        create_response = await client.request(
            method="POST",
            url="/api/notes",
            headers=key_headers,
            json={"title": "API Key Note", "text": "Initial"},
        )
    assert create_response.status_code == status.HTTP_201_CREATED
    note_id = create_response.json()["id"]

    async with api_client(app) as client:
        get_response = await client.request(
            method="GET",
            url="/api/notes",
            headers=key_headers,
        )
    assert get_response.status_code == status.HTTP_200_OK
    assert any(note["id"] == note_id for note in get_response.json())

    async with api_client(app) as client:
        search_response = await client.request(
            method="GET",
            url="/api/notes/search/by-title?query=API Key Note&exact_match=true",
            headers=key_headers,
        )
    assert search_response.status_code == status.HTTP_200_OK
    assert [note["title"] for note in search_response.json()] == ["API Key Note"]

    async with api_client(app) as client:
        update_response = await client.request(
            method="PATCH",
            url=f"/api/notes/{note_id}",
            headers=key_headers,
            json={"title": "API Key Note Updated"},
        )
    assert update_response.status_code == status.HTTP_200_OK
    assert update_response.json()["title"] == "API Key Note Updated"

    async with api_client(app) as client:
        delete_response = await client.request(
            method="DELETE",
            url=f"/api/notes/{note_id}",
            headers=key_headers,
        )
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert await repo_hub.notes.get_by_id(UUID(note_id)) is None


@pytest.mark.asyncio
async def test_invalid_api_key_falls_back_to_bearer_token(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
    user,
):
    # setup: create app and valid bearer token
    config = await dishka_request.get(Config)
    auth_interactor = await dishka_request.get(AuthInteractor)
    tokens = await auth_interactor.login(user.telegram_id)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)

    # action: call notes endpoint with invalid api key and valid bearer token
    async with api_client(app) as client:
        response = await client.request(
            method="GET",
            url="/api/notes",
            headers={
                "X-API-Key": "invalid-api-key",
                "Authorization": f"Bearer {tokens.access_token}",
            },
        )

    # check: request is authorized by bearer fallback
    assert response.status_code == status.HTTP_200_OK
