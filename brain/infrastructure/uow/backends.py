from __future__ import annotations

from typing import Protocol, runtime_checkable

from neo4j import AsyncDriver, AsyncSession as Neo4jAsyncSession, AsyncTransaction
from sqlalchemy.ext.asyncio import AsyncSession

from brain.infrastructure.uow.context import UnitOfWorkContext


@runtime_checkable
class ITransactionController(Protocol):
    backend_key: str

    async def begin(self, context: UnitOfWorkContext) -> None:
        raise NotImplementedError

    async def ensure_started(self, context: UnitOfWorkContext) -> None:
        raise NotImplementedError

    async def commit(self, context: UnitOfWorkContext) -> None:
        raise NotImplementedError

    async def rollback(self, context: UnitOfWorkContext) -> None:
        raise NotImplementedError

    async def close(self, context: UnitOfWorkContext) -> None:
        raise NotImplementedError


@runtime_checkable
class IFlushableTransactionController(Protocol):
    async def flush(self, context: UnitOfWorkContext) -> None:
        raise NotImplementedError


class SqlAlchemyTransactionController(ITransactionController, IFlushableTransactionController):
    backend_key = "sql"

    def __init__(self, session: AsyncSession):
        self._session = session

    async def begin(self, context: UnitOfWorkContext) -> None:
        context.set_handle(self.backend_key, self._session)
        context.mark_started(self.backend_key)

    async def ensure_started(self, context: UnitOfWorkContext) -> None:
        if context.is_started(self.backend_key):
            return
        await self.begin(context)

    async def commit(self, context: UnitOfWorkContext) -> None:
        if not context.is_started(self.backend_key):
            return
        await self._session.commit()

    async def rollback(self, context: UnitOfWorkContext) -> None:
        if not context.is_started(self.backend_key):
            return
        await self._session.rollback()

    async def close(self, context: UnitOfWorkContext) -> None:
        return None

    async def flush(self, context: UnitOfWorkContext) -> None:
        await self.ensure_started(context)
        await self._session.flush()


class Neo4jTransactionController(ITransactionController):
    backend_key = "neo4j"
    _session_key = "neo4j_session"

    def __init__(self, driver: AsyncDriver, database: str):
        self._driver = driver
        self._database = database

    async def begin(self, context: UnitOfWorkContext) -> None:
        return None

    async def ensure_started(self, context: UnitOfWorkContext) -> None:
        if context.is_started(self.backend_key):
            return

        session = self._driver.session(database=self._database)
        tx = await session.begin_transaction()

        context.set_handle(self._session_key, session)
        context.set_handle(self.backend_key, tx)
        context.mark_started(self.backend_key)

    async def commit(self, context: UnitOfWorkContext) -> None:
        if not context.is_started(self.backend_key):
            return
        tx = context.get_handle(self.backend_key)
        if tx is None:
            return
        await tx.commit()

    async def rollback(self, context: UnitOfWorkContext) -> None:
        if not context.is_started(self.backend_key):
            return
        tx = context.get_handle(self.backend_key)
        if tx is None:
            return
        await tx.rollback()

    async def close(self, context: UnitOfWorkContext) -> None:
        session = context.get_handle(self._session_key)
        context.remove_handle(self.backend_key)
        context.remove_handle(self._session_key)
        if session is not None:
            await session.close()

    def get_tx_handle(self, context: UnitOfWorkContext) -> AsyncTransaction | None:
        handle = context.get_handle(self.backend_key)
        if isinstance(handle, AsyncTransaction):
            return handle
        return None

    def get_session_handle(self, context: UnitOfWorkContext) -> Neo4jAsyncSession | None:
        handle = context.get_handle(self._session_key)
        if isinstance(handle, Neo4jAsyncSession):
            return handle
        return None
