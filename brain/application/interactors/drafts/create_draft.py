from uuid import UUID, uuid4

from brain.application.abstractions.repositories.drafts import IDraftsRepository
from brain.application.abstractions.uow import UnitOfWorkFactory
from brain.application.interactors.drafts.dto import CreateDraft
from brain.application.services.draft_hashtag_sync import DraftHashtagSyncService
from brain.domain.entities.draft import Draft


class CreateDraftInteractor:
    def __init__(
        self,
        drafts_repo: IDraftsRepository,
        hashtag_sync_service: DraftHashtagSyncService,
        uow_factory: UnitOfWorkFactory,
    ):
        self._drafts_repo = drafts_repo
        self._hashtag_sync_service = hashtag_sync_service
        self._uow_factory = uow_factory

    async def create_draft(self, draft_data: CreateDraft) -> UUID:
        async with self._uow_factory() as uow:
            draft = Draft(
                id=uuid4(),
                user_id=draft_data.user_id,
                text=draft_data.text,
                file_id=draft_data.file_id,
            )
            await self._drafts_repo.create(draft)
            draft.hashtags = await self._hashtag_sync_service.sync(
                draft_id=draft.id,
                text=draft.text,
            )
            await uow.commit()
            return draft.id
