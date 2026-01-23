from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from brain.domain.entities.note import Note
from brain.domain.entities.graph import GraphData


class INotesGraphRepository(Protocol):
    @abstractmethod
    async def upsert_note(self, note: Note):
        raise NotImplementedError

    @abstractmethod
    async def sync_connections(
        self,
        note: Note,
        link_targets: list[str],
        previous_title: str | None = None,
        previous_represents_keyword_id: UUID | None = None,
    ):
        raise NotImplementedError

    @abstractmethod
    async def delete_note(self, note_id: UUID):
        raise NotImplementedError

    @abstractmethod
    async def count_notes_by_user_and_title(self, user_id: UUID, title: str) -> int:
        raise NotImplementedError

    @abstractmethod
    async def count_links_between_notes(self, user_id: UUID, from_title: str, to_title: str) -> int:
        raise NotImplementedError

    @abstractmethod
    async def get_graph(
        self,
        user_id: UUID,
        query: str | None = None,
        depth: int = 1,
    ) -> GraphData:
        raise NotImplementedError
