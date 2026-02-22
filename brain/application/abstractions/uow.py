from collections.abc import Callable
from types import TracebackType
from typing import Protocol


class IUnitOfWork(Protocol):
    async def __aenter__(self) -> "IUnitOfWork":
        raise NotImplementedError

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        raise NotImplementedError

    async def commit(self) -> None:
        raise NotImplementedError

    async def rollback(self) -> None:
        raise NotImplementedError

    async def flush(self) -> None:
        raise NotImplementedError


UnitOfWorkFactory = Callable[[], IUnitOfWork]
