from brain.application.abstractions.uow import UnitOfWorkFactory
from brain.application.interactors.notes.dto import UpdateNote
from brain.application.services.note_crud import NoteUpdateService
from brain.domain.entities.note import Note


class UpdateNoteInteractor:
    def __init__(
        self,
        note_update_service: NoteUpdateService,
        uow_factory: UnitOfWorkFactory,
    ):
        self._note_update_service = note_update_service
        self._uow_factory = uow_factory

    async def update_note(self, note_data: UpdateNote) -> Note:
        async with self._uow_factory() as uow:
            note = await self._note_update_service.update_note(note_data)
            await uow.commit()
            return note
