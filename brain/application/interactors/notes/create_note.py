from uuid import UUID

from brain.application.abstractions.uow import UnitOfWorkFactory
from brain.application.interactors.notes.dto import CreateNote
from brain.application.services.note_crud import NoteCreationService


class CreateNoteInteractor:
    def __init__(
        self,
        note_creation_service: NoteCreationService,
        uow_factory: UnitOfWorkFactory,
    ):
        self._note_creation_service = note_creation_service
        self._uow_factory = uow_factory

    async def create_note(self, note_data: CreateNote) -> UUID:
        async with self._uow_factory() as uow:
            note_id = await self._note_creation_service.create_note(note_data)
            await uow.commit()
            return note_id
