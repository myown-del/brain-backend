from uuid import UUID

from brain.application.abstractions.uow import UnitOfWorkFactory
from brain.application.services.draft_access import DraftDeletionService


class DeleteDraftInteractor:
    def __init__(
        self,
        draft_deletion_service: DraftDeletionService,
        uow_factory: UnitOfWorkFactory,
    ):
        self._draft_deletion_service = draft_deletion_service
        self._uow_factory = uow_factory

    async def delete_draft(self, draft_id: UUID) -> None:
        async with self._uow_factory() as uow:
            await self._draft_deletion_service.delete_draft(draft_id)
            await uow.commit()
