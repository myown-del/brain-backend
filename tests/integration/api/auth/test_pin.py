import pytest
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from starlette import status

from brain.application.interactors.auth.interactor import AuthInteractor
from brain.config.models import Config
from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from brain.presentation.api.factory import create_bare_app


async def _build_auth_headers(
    dishka_request: AsyncContainer,
    user: User,
) -> dict[str, str]:
    auth_interactor = await dishka_request.get(AuthInteractor)
    tokens = await auth_interactor.login(telegram_id=user.telegram_id)
    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest.mark.asyncio
async def test_set_pin_stores_hashed_pin(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    repo_hub: RepositoryHub,
    api_client,
    user: User,
):
    # setup: create app and authenticated headers
    config = await dishka_request.get(Config)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)
    headers = await _build_auth_headers(dishka_request=dishka_request, user=user)

    # action: set pin
    async with api_client(app) as client:
        response = await client.request(
            method="POST",
            url="/api/auth/pin/set",
            headers=headers,
            json={"pin": "1234"},
        )

    # check: status is no content and pin is stored as hash
    assert response.status_code == status.HTTP_204_NO_CONTENT
    stored_user = await repo_hub.users.get_by_id(entity_id=user.id)
    assert stored_user is not None
    assert stored_user.pin_hash is not None
    assert stored_user.pin_hash != "1234"


@pytest.mark.asyncio
async def test_set_pin_rejects_invalid_pin(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
    user: User,
):
    # setup: create app and authenticated headers
    config = await dishka_request.get(Config)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)
    headers = await _build_auth_headers(dishka_request=dishka_request, user=user)

    # action: set invalid non-digit pin
    async with api_client(app) as client:
        response = await client.request(
            method="POST",
            url="/api/auth/pin/set",
            headers=headers,
            json={"pin": "12ab"},
        )

    # check: validation error
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_set_pin_rejects_short_and_long_pin(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
    user: User,
):
    # setup: create app and authenticated headers
    config = await dishka_request.get(Config)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)
    headers = await _build_auth_headers(dishka_request=dishka_request, user=user)

    async with api_client(app) as client:
        # action: set too-short pin
        short_response = await client.request(
            method="POST",
            url="/api/auth/pin/set",
            headers=headers,
            json={"pin": "123"},
        )
        # action: set too-long pin
        long_response = await client.request(
            method="POST",
            url="/api/auth/pin/set",
            headers=headers,
            json={"pin": "1234567"},
        )

    # check: both are validation errors
    assert short_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert long_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_verify_pin_returns_true_for_correct_pin(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
    user: User,
):
    # setup: create app and authenticated headers
    config = await dishka_request.get(Config)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)
    headers = await _build_auth_headers(dishka_request=dishka_request, user=user)

    # setup: set pin
    async with api_client(app) as client:
        await client.request(
            method="POST",
            url="/api/auth/pin/set",
            headers=headers,
            json={"pin": "1234"},
        )

    # action: verify with matching pin
    async with api_client(app) as client:
        response = await client.request(
            method="POST",
            url="/api/auth/pin/verify",
            headers=headers,
            json={"pin": "1234"},
        )

    # check: verification passed
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"verified": True}


@pytest.mark.asyncio
async def test_verify_pin_returns_false_for_wrong_pin(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
    user: User,
):
    # setup: create app and authenticated headers
    config = await dishka_request.get(Config)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)
    headers = await _build_auth_headers(dishka_request=dishka_request, user=user)

    # setup: set pin
    async with api_client(app) as client:
        await client.request(
            method="POST",
            url="/api/auth/pin/set",
            headers=headers,
            json={"pin": "1234"},
        )

    # action: verify with different pin
    async with api_client(app) as client:
        response = await client.request(
            method="POST",
            url="/api/auth/pin/verify",
            headers=headers,
            json={"pin": "0000"},
        )

    # check: verification failed
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"verified": False}


@pytest.mark.asyncio
async def test_verify_pin_returns_false_when_not_set(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
    user: User,
):
    # setup: create app and authenticated headers
    config = await dishka_request.get(Config)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)
    headers = await _build_auth_headers(dishka_request=dishka_request, user=user)

    # action: verify before pin is configured
    async with api_client(app) as client:
        response = await client.request(
            method="POST",
            url="/api/auth/pin/verify",
            headers=headers,
            json={"pin": "1234"},
        )

    # check: verification failed
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"verified": False}


@pytest.mark.asyncio
async def test_pin_endpoints_require_auth(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
):
    # setup: create app
    config = await dishka_request.get(Config)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)

    # action: call pin endpoints without auth
    async with api_client(app) as client:
        set_response = await client.request(
            method="POST",
            url="/api/auth/pin/set",
            json={"pin": "1234"},
        )
        verify_response = await client.request(
            method="POST",
            url="/api/auth/pin/verify",
            json={"pin": "1234"},
        )

    # check: both requests are unauthorized
    assert set_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert verify_response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_pin_status_reflects_current_user_pin_state(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    api_client,
    user: User,
):
    # setup: create app and authenticated headers
    config = await dishka_request.get(Config)
    app = create_bare_app(config.api)
    setup_dishka(container=dishka, app=app)
    headers = await _build_auth_headers(dishka_request=dishka_request, user=user)

    async with api_client(app) as client:
        # action: read status before pin setup
        before_response = await client.request(
            method="GET",
            url="/api/auth/pin/status",
            headers=headers,
        )

        # setup: configure pin
        await client.request(
            method="POST",
            url="/api/auth/pin/set",
            headers=headers,
            json={"pin": "1234"},
        )

        # action: read status after pin setup
        after_response = await client.request(
            method="GET",
            url="/api/auth/pin/status",
            headers=headers,
        )

    # check: status changes to configured
    assert before_response.status_code == status.HTTP_200_OK
    assert before_response.json() == {"is_pin_set": False}
    assert after_response.status_code == status.HTTP_200_OK
    assert after_response.json() == {"is_pin_set": True}
