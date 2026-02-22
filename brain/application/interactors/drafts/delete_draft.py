from uuid import UUID

from brain.application.services.draft_access import DraftDeletionService


class DeleteDraftInteractor:
    def __init__(self, draft_deletion_service: DraftDeletionService):
        self._draft_deletion_service = draft_deletion_service

    async def delete_draft(self, draft_id: UUID) -> None:
        await self._draft_deletion_service.delete_draft(draft_id)
