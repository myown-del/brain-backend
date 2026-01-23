import os

from testcontainers.neo4j import Neo4jContainer

from dishka import Provider, Scope, provide

from typing import AsyncIterable

from neo4j import AsyncDriver

from brain.application.abstractions.config.models import INeo4jConfig
from brain.application.abstractions.repositories.notes_graph import INotesGraphRepository
from brain.config.models import Config
from brain.infrastructure.graph.connection import create_driver
from brain.infrastructure.graph.repositories.notes import NotesGraphRepository
from tests.mocks.config import Neo4jConfig


class TestGraphProvider(Provider):
    scope = Scope.APP

    @provide(scope=Scope.APP)
    async def get_driver(self, config: INeo4jConfig) -> AsyncIterable[AsyncDriver]:
        driver = create_driver(config)
        yield driver
        await driver.close()

    @provide(scope=Scope.REQUEST, provides=INotesGraphRepository)
    def get_notes_graph_repo(
        self, driver: AsyncDriver, config: INeo4jConfig,
    ) -> NotesGraphRepository:
        return NotesGraphRepository(driver=driver, database=config.database)


class TestNeo4jConfigProvider(Provider):
    scope = Scope.APP

    @provide(provides=INeo4jConfig)
    def get_neo4j_config(self, config: Config) -> Neo4jConfig:
        neo4j = Neo4jContainer("neo4j:5")
        if os.name == "nt":
            neo4j.get_container_host_ip = lambda: "localhost"
        try:
            neo4j.start()
            if hasattr(neo4j, "get_connection_url"):
                uri = neo4j.get_connection_url()
            else:
                host = neo4j.get_container_host_ip()
                port = neo4j.get_exposed_port(7687)
                uri = f"bolt://{host}:{port}"

            password = "neo4j"
            if hasattr(neo4j, "get_admin_password"):
                password = neo4j.get_admin_password()
            elif hasattr(neo4j, "password"):
                password = neo4j.password

            user = getattr(neo4j, "username", None) or "neo4j"

            neo4j_config = Neo4jConfig(
                uri=uri,
                user=user,
                password=password,
                database="neo4j",
            )
            config.neo4j = neo4j_config
            yield neo4j_config
        finally:
            neo4j.stop()
