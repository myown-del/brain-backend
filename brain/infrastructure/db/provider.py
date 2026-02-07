from typing import AsyncIterable

from dishka import Provider, provide, Scope
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncEngine

from brain.application.abstractions.repositories.notes import INotesRepository
from brain.application.abstractions.repositories.keywords import IKeywordsRepository
from brain.application.abstractions.repositories.users import IUsersRepository
from brain.application.abstractions.repositories.s3_files import (
    IS3FilesRepository,
)
from brain.application.abstractions.repositories.jwt import (
    IJwtRefreshTokensRepository,
)
from brain.application.abstractions.repositories.api_keys import (
    IApiKeysRepository,
)
from brain.application.abstractions.repositories.tg_bot_auth import (
    ITelegramBotAuthSessionsRepository,
)
from brain.application.abstractions.config.models import IDatabaseConfig
from brain.infrastructure.db.connection import create_engine, create_session_maker
from brain.infrastructure.db.repositories.hub import RepositoryHub
from brain.infrastructure.db.repositories.notes import NotesRepository
from brain.infrastructure.db.repositories.keywords import KeywordsRepository
from brain.infrastructure.db.repositories.users import UsersRepository
from brain.infrastructure.db.repositories.s3_files import S3FilesRepository
from brain.infrastructure.db.repositories.jwt import (
    JwtRefreshTokensRepository,
)
from brain.infrastructure.db.repositories.api_keys import (
    ApiKeysRepository,
)
from brain.infrastructure.db.repositories.tg_bot_auth import (
    TelegramBotAuthSessionsRepository,
)


class DatabaseProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_engine(self, config: IDatabaseConfig) -> AsyncIterable[AsyncEngine]:
        engine = create_engine(config)
        yield engine
        # await engine.dispose(True)

    @provide
    def get_pool(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return create_session_maker(engine)

    @provide(scope=Scope.REQUEST)
    async def get_session(self, pool: async_sessionmaker[AsyncSession]) -> AsyncIterable[AsyncSession]:
        async with pool() as session:
            yield session

    users_repository = provide(UsersRepository, scope=Scope.REQUEST, provides=IUsersRepository)
    notes_repository = provide(NotesRepository, scope=Scope.REQUEST, provides=INotesRepository)
    keywords_repository = provide(KeywordsRepository, scope=Scope.REQUEST, provides=IKeywordsRepository)
    s3_files_repository = provide(S3FilesRepository, scope=Scope.REQUEST, provides=IS3FilesRepository)
    tg_bot_auth_repository = provide(
        TelegramBotAuthSessionsRepository,
        scope=Scope.REQUEST,
        provides=ITelegramBotAuthSessionsRepository,
    )
    jwt_repository = provide(
        JwtRefreshTokensRepository,
        scope=Scope.REQUEST,
        provides=IJwtRefreshTokensRepository,
    )
    api_keys_repository = provide(
        ApiKeysRepository,
        scope=Scope.REQUEST,
        provides=IApiKeysRepository,
    )
    hub_repository = provide(RepositoryHub, scope=Scope.REQUEST)
