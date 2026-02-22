from typing import AsyncIterable
from collections.abc import Callable

from dishka import Provider, provide, Scope
from neo4j import AsyncDriver
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncEngine

from brain.application.abstractions.config.models import INeo4jConfig
from brain.application.abstractions.repositories.drafts import IDraftsRepository
from brain.application.abstractions.repositories.hashtags import IHashtagsRepository
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
from brain.application.abstractions.uow import IUnitOfWork, UnitOfWorkFactory
from brain.infrastructure.db.connection import create_engine, create_session_maker
from brain.infrastructure.db.repositories.hub import RepositoryHub
from brain.infrastructure.db.repositories.drafts import DraftsRepository
from brain.infrastructure.db.repositories.hashtags import HashtagsRepository
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
from brain.infrastructure.uow.composite import CompositeUnitOfWork
from brain.infrastructure.uow.context import UnitOfWorkContext
from brain.infrastructure.uow.backends import (
    Neo4jTransactionController,
    SqlAlchemyTransactionController,
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

    @provide(scope=Scope.REQUEST)
    def get_uow_context(self) -> UnitOfWorkContext:
        return UnitOfWorkContext()

    @provide(scope=Scope.REQUEST)
    def get_sql_transaction_controller(
        self,
        session: AsyncSession,
    ) -> SqlAlchemyTransactionController:
        return SqlAlchemyTransactionController(session=session)

    @provide(scope=Scope.REQUEST)
    def get_neo4j_transaction_controller(
        self,
        driver: AsyncDriver,
        neo4j_config: INeo4jConfig,
    ) -> Neo4jTransactionController:
        return Neo4jTransactionController(
            driver=driver,
            database=neo4j_config.database,
        )

    @provide(scope=Scope.REQUEST, provides=UnitOfWorkFactory)
    def get_uow_factory(
        self,
        sql_controller: SqlAlchemyTransactionController,
        neo4j_controller: Neo4jTransactionController,
        uow_context: UnitOfWorkContext,
    ) -> Callable[[], IUnitOfWork]:
        def factory() -> IUnitOfWork:
            return CompositeUnitOfWork(
                controllers=[sql_controller, neo4j_controller],
                uow_context=uow_context,
                primary_flush_controller_key=SqlAlchemyTransactionController.backend_key,
            )

        return factory

    users_repository = provide(UsersRepository, scope=Scope.REQUEST, provides=IUsersRepository)
    drafts_repository = provide(DraftsRepository, scope=Scope.REQUEST, provides=IDraftsRepository)
    hashtags_repository = provide(HashtagsRepository, scope=Scope.REQUEST, provides=IHashtagsRepository)
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
