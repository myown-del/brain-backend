from contextlib import asynccontextmanager
from collections.abc import AsyncIterator, Callable

import pytest
import pytest_asyncio
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from brain.config.models import Config
from brain.domain.entities.user import User
from brain.presentation.api.dependencies.auth import (
    get_notes_user_from_request,
    get_user_from_request,
)
from brain.presentation.api.factory import create_bare_app

ApiClientFactory = Callable[[FastAPI], AsyncIterator[AsyncClient]]


@pytest.fixture
def api_client() -> ApiClientFactory:
    @asynccontextmanager
    async def _client(app: FastAPI) -> AsyncIterator[AsyncClient]:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    return _client


@pytest_asyncio.fixture
async def notes_app(
    dishka: AsyncContainer,
    dishka_request: AsyncContainer,
    user: User,
) -> FastAPI:
    config = await dishka_request.get(Config)
    app = create_bare_app(config.api)

    async def override_user() -> User:
        return user

    app.dependency_overrides[get_user_from_request] = override_user
    app.dependency_overrides[get_notes_user_from_request] = override_user
    setup_dishka(container=dishka, app=app)
    return app
