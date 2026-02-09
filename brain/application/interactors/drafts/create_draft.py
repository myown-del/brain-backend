from uuid import UUID, uuid4

from brain.application.abstractions.repositories.drafts import IDraftsRepository
from brain.application.interactors.drafts.dto import CreateDraft
from brain.application.services.draft_hashtag_sync import DraftHashtagSyncService
from brain.domain.entities.draft import Draft


class CreateDraftInteractor:
    def __init__(
        self,
        drafts_repo: IDraftsRepository,
        hashtag_sync_service: DraftHashtagSyncService,
    ):
        self._drafts_repo = drafts_repo
        self._hashtag_sync_service = hashtag_sync_service

    async def create_draft(self, draft_data: CreateDraft) -> UUID:
        draft = Draft(
            id=uuid4(),
            user_id=draft_data.user_id,
            text=draft_data.text,
        )
        await self._drafts_repo.create(draft)
        draft.hashtags = await self._hashtag_sync_service.sync(
            draft_id=draft.id,
            text=draft.text,
        )
        return draft.id
