from uuid import UUID

from brain.application.services.note_crud import NoteDeletionService


class DeleteNoteInteractor:
    def __init__(self, note_deletion_service: NoteDeletionService):
        self._note_deletion_service = note_deletion_service

    async def delete_note(self, note_id: UUID) -> None:
        await self._note_deletion_service.delete_note(note_id)
