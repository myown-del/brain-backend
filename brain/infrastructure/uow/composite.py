from types import TracebackType

from brain.application.abstractions.uow import IUnitOfWork
from brain.infrastructure.uow.context import UnitOfWorkContext
from brain.infrastructure.uow.backends import (
    IFlushableTransactionController,
    ITransactionController,
)


class CompositeUnitOfWork(IUnitOfWork):
    def __init__(
        self,
        controllers: list[ITransactionController],
        uow_context: UnitOfWorkContext,
        primary_flush_controller_key: str = "sql",
    ):
        self._controllers = controllers
        self._uow_context = uow_context
        self._primary_flush_controller_key = primary_flush_controller_key
        self._committed = False
        self._rolled_back = False

    async def __aenter__(self) -> "CompositeUnitOfWork":
        self._committed = False
        self._rolled_back = False
        self._uow_context.clear()
        for controller in self._controllers:
            await controller.begin(self._uow_context)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        try:
            if exc_type is not None and not self._committed and not self._rolled_back:
                await self.rollback()
        finally:
            self._uow_context.clear()

    async def commit(self) -> None:
        if self._committed or self._rolled_back:
            return

        try:
            for controller in self._controllers:
                await controller.commit(self._uow_context)
        finally:
            for controller in reversed(self._controllers):
                await controller.close(self._uow_context)

        self._committed = True
        self._uow_context.mark_committed()

    async def rollback(self) -> None:
        if self._rolled_back or self._committed:
            return

        try:
            for controller in reversed(self._controllers):
                await controller.rollback(self._uow_context)
        finally:
            for controller in reversed(self._controllers):
                await controller.close(self._uow_context)

        self._rolled_back = True
        self._uow_context.mark_rolled_back()

    async def flush(self) -> None:
        for controller in self._controllers:
            if controller.backend_key != self._primary_flush_controller_key:
                continue
            if isinstance(controller, IFlushableTransactionController):
                await controller.flush(self._uow_context)
                return
