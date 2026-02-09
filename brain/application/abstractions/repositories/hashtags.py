from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from brain.domain.entities.hashtag import Hashtag


class IHashtagsRepository(Protocol):
    @abstractmethod
    async def ensure_hashtags(self, texts: list[str]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def replace_draft_hashtags(self, draft_id: UUID, texts: list[str]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_draft_hashtags(self, draft_id: UUID) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_text(self, text: str) -> Hashtag | None:
        raise NotImplementedError
