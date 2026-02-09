from uuid import UUID

from brain.application.abstractions.repositories.drafts import IDraftsRepository
from brain.domain.entities.draft import Draft


class GetDraftInteractor:
    def __init__(self, drafts_repo: IDraftsRepository):
        self._drafts_repo = drafts_repo

    async def get_draft_by_id(self, draft_id: UUID) -> Draft | None:
        return await self._drafts_repo.get_by_id(draft_id)
