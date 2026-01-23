from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from alembic.command import upgrade
from dishka import AsyncContainer, make_async_container
from alembic.config import Config as AlembicConfig

from brain.application.abstractions.config.models import IDatabaseConfig
from brain.application.interactors.factory import InteractorProvider
from brain.config.models import Config
from brain.config.parser import load_config
from brain.config.provider import ConfigProvider
from brain.domain.entities.user import User
from brain.infrastructure.db.provider import DatabaseProvider
from brain.infrastructure.db.repositories.hub import RepositoryHub
from brain.infrastructure.jwt.provider import JwtProvider
from tests.fixtures.db_provider import TestDbProvider
from tests.fixtures.profile_picture_storage_provider import TestProfilePictureStorageProvider
from tests.fixtures.graph_provider import TestGraphProvider, TestNeo4jConfigProvider
from tests.fixtures.profile_picture_provider import TestProfilePictureProvider
from tests.fixtures.bot_provider import MockBotProvider


@pytest_asyncio.fixture(scope="session")
async def alembic_config(dishka: AsyncContainer) -> AlembicConfig:
    alembic_cfg = AlembicConfig("alembic.ini")
    alembic_cfg.set_main_option(
        "script_location",
        str(Path("brain") / "infrastructure" / "migrations"),
    )
    db_config = await dishka.get(IDatabaseConfig)
    alembic_cfg.set_main_option("sqlalchemy.url", db_config.uri)
    return alembic_cfg


@pytest_asyncio.fixture(scope="session")
async def dishka():
    config = load_config(
        config_class=Config,
        env_file_path="tests/.env",
    )
    container = make_async_container(
        ConfigProvider(),
        TestDbProvider(),
        DatabaseProvider(),
        TestNeo4jConfigProvider(),
        TestGraphProvider(),
        TestProfilePictureStorageProvider(),
        TestProfilePictureProvider(),
        MockBotProvider(),
        InteractorProvider(),
        JwtProvider(),
        context={Config: config},
    )
    yield container
    await container.close()


@pytest.fixture(scope="session", autouse=True)
def upgrade_schema_db(alembic_config: AlembicConfig):
    upgrade(alembic_config, "head")


@pytest_asyncio.fixture
async def dishka_request(dishka: AsyncContainer) -> AsyncContainer:
    async with dishka() as request_container:
        yield request_container


async def clear_db(repo_hub: RepositoryHub):
    await repo_hub.s3_files.delete_all()
    await repo_hub.users.delete_all()
    await repo_hub.notes.delete_all()


@pytest_asyncio.fixture
async def repo_hub(dishka_request: AsyncContainer) -> RepositoryHub:
    repo_hub_ = await dishka_request.get(RepositoryHub)
    await clear_db(repo_hub_)
    return repo_hub_


@pytest_asyncio.fixture
async def user(repo_hub: RepositoryHub) -> User:
    user = User(
        id=uuid4(),
        telegram_id=123,
        username="test_username",
        first_name="John",
        last_name="Smith",
    )
    await repo_hub.users.create(user)
    return user
