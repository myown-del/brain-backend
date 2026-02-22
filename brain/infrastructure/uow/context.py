from __future__ import annotations

from contextvars import ContextVar
from typing import Any


class UnitOfWorkContext:
    def __init__(self) -> None:
        self._handles: ContextVar[dict[str, Any]] = ContextVar("uow_handles", default={})
        self._started: ContextVar[set[str]] = ContextVar("uow_started_backends", default=set())
        self._committed: ContextVar[bool] = ContextVar("uow_committed", default=False)
        self._rolled_back: ContextVar[bool] = ContextVar("uow_rolled_back", default=False)

    def set_handle(self, key: str, handle: Any) -> None:
        handles = dict(self._handles.get())
        handles[key] = handle
        self._handles.set(handles)

    def get_handle(self, key: str) -> Any | None:
        return self._handles.get().get(key)

    def has_handle(self, key: str) -> bool:
        return key in self._handles.get()

    def remove_handle(self, key: str) -> None:
        handles = dict(self._handles.get())
        handles.pop(key, None)
        self._handles.set(handles)

    def mark_started(self, key: str) -> None:
        started = set(self._started.get())
        started.add(key)
        self._started.set(started)

    def is_started(self, key: str) -> bool:
        return key in self._started.get()

    def started_backends(self) -> set[str]:
        return set(self._started.get())

    def mark_committed(self) -> None:
        self._committed.set(True)

    def mark_rolled_back(self) -> None:
        self._rolled_back.set(True)

    def is_committed(self) -> bool:
        return self._committed.get()

    def is_rolled_back(self) -> bool:
        return self._rolled_back.get()

    def clear(self) -> None:
        self._handles.set({})
        self._started.set(set())
        self._committed.set(False)
        self._rolled_back.set(False)
