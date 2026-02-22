from uuid import UUID

from brain.application.abstractions.repositories.notes import INotesRepository
from brain.domain.entities.note import Note


class NoteLookupService:
    def __init__(self, notes_repo: INotesRepository):
        self._notes_repo = notes_repo

    async def get_note_by_id(self, note_id: UUID) -> Note | None:
        return await self._notes_repo.get_by_id(note_id)

    async def get_note_by_title(self, user_id: UUID, title: str, exact_match: bool = False) -> Note | None:
        return await self._notes_repo.get_by_title(user_id, title, exact_match)
