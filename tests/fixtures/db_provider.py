import logging
import os

from dishka import Provider, Scope, provide
from testcontainers.postgres import PostgresContainer

from brain.application.abstractions.config.models import IDatabaseConfig
from brain.config.models import Config
from tests.mocks.config import DatabaseConfig

logger = logging.getLogger(__name__)


class TestDbProvider(Provider):
    scope = Scope.APP

    @provide(provides=IDatabaseConfig)
    def get_db_config(self, config: Config) -> DatabaseConfig:  # pyright: ignore[reportInvalidTypeForm]
        postgres = PostgresContainer("postgres:16.1")
        if os.name == "nt":
            postgres.get_container_host_ip = lambda: "localhost"
        try:
            postgres.start()
            postgres_url_ = postgres.get_connection_url().replace("psycopg2", "asyncpg")
            db_config = DatabaseConfig(uri_=postgres_url_)
            config.db = db_config
            yield db_config
        finally:
            postgres.stop()
