from abc import abstractmethod
from datetime import datetime
from typing import Protocol
from uuid import UUID

from brain.domain.entities.draft import Draft


class IDraftsRepository(Protocol):
    @abstractmethod
    async def create(self, entity: Draft) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, draft_id: UUID) -> Draft | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_user(
        self,
        user_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        hashtags: list[str] | None = None,
    ) -> list[Draft]:
        raise NotImplementedError

    @abstractmethod
    async def search_by_text(
        self,
        user_id: UUID,
        query: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        hashtags: list[str] | None = None,
    ) -> list[Draft]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, entity: Draft) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_id(self, draft_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_all(self) -> None:
        raise NotImplementedError
