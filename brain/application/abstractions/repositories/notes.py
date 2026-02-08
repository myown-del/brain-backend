from abc import ABC, abstractmethod
from datetime import datetime
from typing import Protocol
from uuid import UUID

from brain.domain.entities.note import Note
from brain.application.abstractions.repositories.models import (
    WikilinkSuggestion,
    NoteCreationStat,
)


class INotesRepository(Protocol):
    """
    Интерфейс репозитория заметок
    """

    @abstractmethod
    async def create(self, entity: Note):
        raise NotImplementedError

    @abstractmethod
    async def get_by_user_telegram_id(
        self,
        telegram_id: int,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        pinned_first: bool = True,
    ) -> list[Note]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Note:
        raise NotImplementedError

    @abstractmethod
    async def get_by_title(self, user_id: UUID, title: str, exact_match: bool = False) -> Note | None:
        raise NotImplementedError

    @abstractmethod
    async def search_by_title(
        self,
        user_id: UUID,
        query: str,
        exact_match: bool = False,
        pinned_first: bool = True,
    ) -> list[Note]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, entity: Note):
        raise NotImplementedError

    @abstractmethod
    async def delete_all(self):
        raise NotImplementedError

    @abstractmethod
    async def delete_by_id(self, entity_id: UUID):
        raise NotImplementedError

    @abstractmethod
    async def count_notes_by_user_and_title(
        self,
        user_id: UUID,
        title: str,
        exclude_note_id: UUID | None = None,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def count_keyword_notes_by_user_and_title(
        self,
        user_id: UUID,
        title: str,
        exclude_note_id: UUID | None = None,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def count_keyword_notes_by_user_and_keyword_id(
        self,
        user_id: UUID,
        keyword_id: UUID,
        exclude_note_id: UUID | None = None,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def search_wikilink_suggestions(
        self,
        user_id: UUID,
        query: str,
    ) -> list[WikilinkSuggestion]:
        raise NotImplementedError

    @abstractmethod
    async def get_note_creation_stats_by_user_telegram_id(
        self,
        telegram_id: int,
    ) -> list[NoteCreationStat]:
        raise NotImplementedError
