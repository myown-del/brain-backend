from uuid import UUID

from brain.application.interactors.notes.dto import CreateNote
from brain.application.services.note_crud import NoteCreationService


class CreateNoteInteractor:
    def __init__(self, note_creation_service: NoteCreationService):
        self._note_creation_service = note_creation_service

    async def create_note(self, note_data: CreateNote) -> UUID:
        return await self._note_creation_service.create_note(note_data)
