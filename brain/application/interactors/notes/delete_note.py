from uuid import UUID

from brain.application.abstractions.uow import UnitOfWorkFactory
from brain.application.services.note_crud import NoteDeletionService


class DeleteNoteInteractor:
    def __init__(
        self,
        note_deletion_service: NoteDeletionService,
        uow_factory: UnitOfWorkFactory,
    ):
        self._note_deletion_service = note_deletion_service
        self._uow_factory = uow_factory

    async def delete_note(self, note_id: UUID) -> None:
        async with self._uow_factory() as uow:
            await self._note_deletion_service.delete_note(note_id)
            await uow.commit()
