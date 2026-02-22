from brain.application.interactors.notes.dto import UpdateNote
from brain.application.services.note_crud import NoteUpdateService
from brain.domain.entities.note import Note


class UpdateNoteInteractor:
    def __init__(self, note_update_service: NoteUpdateService):
        self._note_update_service = note_update_service

    async def update_note(self, note_data: UpdateNote) -> Note:
        return await self._note_update_service.update_note(note_data)
