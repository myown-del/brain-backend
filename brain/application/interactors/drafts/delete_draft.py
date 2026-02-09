from uuid import UUID

from brain.application.abstractions.repositories.drafts import IDraftsRepository
from brain.application.interactors.drafts.exceptions import DraftNotFoundException


class DeleteDraftInteractor:
    def __init__(self, drafts_repo: IDraftsRepository):
        self._drafts_repo = drafts_repo

    async def delete_draft(self, draft_id: UUID) -> None:
        draft = await self._drafts_repo.get_by_id(draft_id)
        if draft is None:
            raise DraftNotFoundException()
        await self._drafts_repo.delete_by_id(draft_id)
