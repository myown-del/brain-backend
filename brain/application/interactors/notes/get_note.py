from uuid import UUID

from brain.application.services.note_lookup import NoteLookupService
from brain.domain.entities.note import Note


class GetNoteInteractor:
    def __init__(self, note_lookup_service: NoteLookupService):
        self._note_lookup_service = note_lookup_service

    async def get_note_by_id(self, note_id: UUID) -> Note | None:
        return await self._note_lookup_service.get_note_by_id(note_id)

    async def get_note_by_title(self, user_id: UUID, title: str, exact_match: bool = False) -> Note | None:
        return await self._note_lookup_service.get_note_by_title(user_id, title, exact_match)
