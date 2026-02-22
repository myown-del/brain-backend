from neo4j import AsyncTransaction

from brain.infrastructure.uow.backends import Neo4jTransactionController
from brain.infrastructure.uow.context import UnitOfWorkContext


class Neo4jTxAccessor:
    def __init__(
        self,
        uow_context: UnitOfWorkContext,
        controller: Neo4jTransactionController,
    ):
        self._uow_context = uow_context
        self._controller = controller

    async def get_tx(self) -> AsyncTransaction:
        await self._controller.ensure_started(self._uow_context)
        tx = self._uow_context.get_handle(self._controller.backend_key)
        if tx is None:
            raise RuntimeError("Neo4j transaction handle is not available")
        return tx
