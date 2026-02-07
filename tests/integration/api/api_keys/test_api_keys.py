import re
from uuid import uuid4

import pytest
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from starlette import status

from brain.application.interactors.auth.interactor import AuthInteractor
from brain.config.models import Config
from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from brain.presentation.api.factory import create_bare_app


@pytest.mark.asyncio
async def test_create_api_key_returns_raw_key(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
    user,
):
    # setup: create app and user access token
    config = await dishka_request.get(Config)
    auth_interactor = await dishka_request.get(AuthInteractor)
    tokens = await auth_interactor.login(user.telegram_id)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)

    # action: create api key
    async with api_client(app) as client:
        response = await client.request(
            method="POST",
            url="/api/api-keys/",
            headers={"Authorization": f"Bearer {tokens.access_token}"},
            json={"name": "integration-key"},
        )

    # check: key payload is returned once with expected format
    assert response.status_code == status.HTTP_201_CREATED
    payload = response.json()
    assert payload["name"] == "integration-key"
    assert re.fullmatch(r"[A-Za-z0-9]{32}", payload["key"])


@pytest.mark.asyncio
async def test_create_api_key_rejects_invalid_jwt(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
):
    # setup: create app with full container
    config = await dishka_request.get(Config)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)

    # action: create api key with invalid access token
    async with api_client(app) as client:
        response = await client.request(
            method="POST",
            url="/api/api-keys/",
            headers={"Authorization": "Bearer invalid.token.here"},
            json={"name": "integration-key"},
        )

    # check: unauthorized response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_api_keys_returns_only_current_user_keys(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    # setup: app and first user token
    config = await dishka_request.get(Config)
    auth_interactor = await dishka_request.get(AuthInteractor)
    user_tokens = await auth_interactor.login(user.telegram_id)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)

    # setup: create two keys for current user
    async with api_client(app) as client:
        await client.request(
            method="POST",
            url="/api/api-keys/",
            headers={"Authorization": f"Bearer {user_tokens.access_token}"},
            json={"name": "user-key-1"},
        )
        await client.request(
            method="POST",
            url="/api/api-keys/",
            headers={"Authorization": f"Bearer {user_tokens.access_token}"},
            json={"name": "user-key-2"},
        )

    # setup: create another user and one key for them
    other_user = User(
        id=uuid4(),
        telegram_id=456,
        username="other",
        first_name="Other",
        last_name="User",
    )
    await repo_hub.users.create(entity=other_user)
    other_tokens = await auth_interactor.login(other_user.telegram_id)
    async with api_client(app) as client:
        await client.request(
            method="POST",
            url="/api/api-keys/",
            headers={"Authorization": f"Bearer {other_tokens.access_token}"},
            json={"name": "other-key"},
        )

    # action: list keys as current user
    async with api_client(app) as client:
        response = await client.request(
            method="GET",
            url="/api/api-keys/",
            headers={"Authorization": f"Bearer {user_tokens.access_token}"},
        )

    # check: only current user keys are returned
    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    names = {key["name"] for key in payload}
    assert names == {"user-key-1", "user-key-2"}
    assert all("key" not in item for item in payload)


@pytest.mark.asyncio
async def test_delete_api_key_deletes_owned_key(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
    user,
):
    # setup: app, token, and api key
    config = await dishka_request.get(Config)
    auth_interactor = await dishka_request.get(AuthInteractor)
    tokens = await auth_interactor.login(user.telegram_id)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)

    async with api_client(app) as client:
        create_response = await client.request(
            method="POST",
            url="/api/api-keys/",
            headers={"Authorization": f"Bearer {tokens.access_token}"},
            json={"name": "to-delete"},
        )
    api_key_id = create_response.json()["id"]

    # action: delete key
    async with api_client(app) as client:
        delete_response = await client.request(
            method="DELETE",
            url=f"/api/api-keys/{api_key_id}",
            headers={"Authorization": f"Bearer {tokens.access_token}"},
        )

    # check: deleted and no longer listed
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    async with api_client(app) as client:
        list_response = await client.request(
            method="GET",
            url="/api/api-keys/",
            headers={"Authorization": f"Bearer {tokens.access_token}"},
        )
    assert list_response.status_code == status.HTTP_200_OK
    assert all(item["id"] != api_key_id for item in list_response.json())


@pytest.mark.asyncio
async def test_delete_api_key_returns_not_found_for_foreign_key(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    # setup: app and users
    config = await dishka_request.get(Config)
    auth_interactor = await dishka_request.get(AuthInteractor)
    user_tokens = await auth_interactor.login(user.telegram_id)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)

    other_user = User(
        id=uuid4(),
        telegram_id=654,
        username="other",
        first_name="Other",
        last_name="User",
    )
    await repo_hub.users.create(entity=other_user)
    other_tokens = await auth_interactor.login(other_user.telegram_id)

    # setup: create key belonging to other user
    async with api_client(app) as client:
        create_response = await client.request(
            method="POST",
            url="/api/api-keys/",
            headers={"Authorization": f"Bearer {other_tokens.access_token}"},
            json={"name": "foreign-key"},
        )
    foreign_key_id = create_response.json()["id"]

    # action: current user tries deleting foreign key
    async with api_client(app) as client:
        delete_response = await client.request(
            method="DELETE",
            url=f"/api/api-keys/{foreign_key_id}",
            headers={"Authorization": f"Bearer {user_tokens.access_token}"},
        )

    # check: not found for non-owned key
    assert delete_response.status_code == status.HTTP_404_NOT_FOUND
    assert delete_response.json()["detail"] == "Api key not found"


@pytest.mark.asyncio
async def test_validate_api_key_returns_true_for_valid_key(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
    user,
):
    # setup: create app, token, and api key
    config = await dishka_request.get(Config)
    auth_interactor = await dishka_request.get(AuthInteractor)
    tokens = await auth_interactor.login(user.telegram_id)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)

    async with api_client(app) as client:
        create_response = await client.request(
            method="POST",
            url="/api/api-keys/",
            headers={"Authorization": f"Bearer {tokens.access_token}"},
            json={"name": "validation-key"},
        )
    api_key = create_response.json()["key"]

    # action: validate the key via dedicated endpoint
    async with api_client(app) as client:
        validate_response = await client.request(
            method="GET",
            url="/api/api-keys/validate",
            headers={"X-API-Key": api_key},
        )

    # check: key is recognized as valid
    assert validate_response.status_code == status.HTTP_200_OK
    assert validate_response.json() == {"is_valid": True}


@pytest.mark.asyncio
async def test_validate_api_key_returns_401_for_invalid_key(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
):
    # setup: create app with full container
    config = await dishka_request.get(Config)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)

    # action: validate unknown key
    async with api_client(app) as client:
        response = await client.request(
            method="GET",
            url="/api/api-keys/validate",
            headers={"X-API-Key": "invalid-api-key"},
        )

    # check: invalid key is rejected
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid api key"
