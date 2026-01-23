from typing import AsyncIterable

from dishka import Provider, provide, Scope
from neo4j import AsyncDriver

from brain.application.abstractions.config.models import INeo4jConfig
from brain.application.abstractions.repositories.notes_graph import INotesGraphRepository
from brain.infrastructure.graph.connection import create_driver
from brain.infrastructure.graph.repositories.notes import NotesGraphRepository


class Neo4jProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_driver(self, config: INeo4jConfig) -> AsyncIterable[AsyncDriver]:
        driver = create_driver(config)
        yield driver
        await driver.close()

    @provide(scope=Scope.REQUEST, provides=INotesGraphRepository)
    def get_notes_graph_repository(self, driver: AsyncDriver, config: INeo4jConfig) -> NotesGraphRepository:
        return NotesGraphRepository(driver=driver, database=config.database)
