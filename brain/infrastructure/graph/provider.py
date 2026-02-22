from typing import AsyncIterable

from dishka import Provider, provide, Scope
from neo4j import AsyncDriver

from brain.application.abstractions.config.models import INeo4jConfig
from brain.application.abstractions.repositories.notes_graph import INotesGraphRepository
from brain.infrastructure.graph.connection import create_driver
from brain.infrastructure.graph.repositories.notes import NotesGraphRepository
from brain.infrastructure.graph.tx_accessor import Neo4jTxAccessor
from brain.infrastructure.uow.backends import Neo4jTransactionController
from brain.infrastructure.uow.context import UnitOfWorkContext


class Neo4jProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_driver(self, config: INeo4jConfig) -> AsyncIterable[AsyncDriver]:
        driver = create_driver(config)
        yield driver
        await driver.close()

    @provide(scope=Scope.REQUEST, provides=INotesGraphRepository)
    def get_notes_graph_repository(
        self,
        driver: AsyncDriver,
        config: INeo4jConfig,
        tx_accessor: Neo4jTxAccessor,
    ) -> NotesGraphRepository:
        return NotesGraphRepository(
            driver=driver,
            database=config.database,
            tx_accessor=tx_accessor,
        )

    @provide(scope=Scope.REQUEST)
    def get_neo4j_tx_accessor(
        self,
        uow_context: UnitOfWorkContext,
        controller: Neo4jTransactionController,
    ) -> Neo4jTxAccessor:
        return Neo4jTxAccessor(
            uow_context=uow_context,
            controller=controller,
        )
