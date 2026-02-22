from uuid import UUID

from brain.application.services.draft_access import DraftLookupService
from brain.domain.entities.draft import Draft


class GetDraftInteractor:
    def __init__(self, draft_lookup_service: DraftLookupService):
        self._draft_lookup_service = draft_lookup_service

    async def get_draft_by_id(self, draft_id: UUID) -> Draft | None:
        return await self._draft_lookup_service.get_draft_by_id(draft_id)
