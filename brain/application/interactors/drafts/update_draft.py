from brain.application.abstractions.repositories.drafts import IDraftsRepository
from brain.application.interactors.drafts.dto import UpdateDraft
from brain.application.interactors.drafts.exceptions import (
    DraftNotFoundException,
    DraftPatchApplyException,
)
from brain.application.services.draft_hashtag_sync import DraftHashtagSyncService
from brain.application.types import Unset
from brain.domain.entities.draft import Draft
from brain.domain.time import utc_now
from brain.domain.services.diffs import apply_patch


class UpdateDraftInteractor:
    def __init__(
        self,
        drafts_repo: IDraftsRepository,
        hashtag_sync_service: DraftHashtagSyncService,
    ):
        self._drafts_repo = drafts_repo
        self._hashtag_sync_service = hashtag_sync_service

    async def update_draft(self, draft_data: UpdateDraft) -> Draft:
        draft = await self._drafts_repo.get_by_id(draft_data.draft_id)
        if draft is None:
            raise DraftNotFoundException()

        if draft_data.patch is not Unset and draft_data.patch is not None:
            try:
                draft.text = apply_patch(draft.text or "", draft_data.patch)
            except Exception as exc:
                raise DraftPatchApplyException() from exc
        elif draft_data.text is not Unset:
            draft.text = draft_data.text
        if draft_data.file_id is not Unset:
            draft.file_id = draft_data.file_id

        draft.updated_at = utc_now()
        await self._drafts_repo.update(draft)
        hashtags = await self._hashtag_sync_service.sync(
            draft_id=draft.id,
            text=draft.text,
        )
        updated_draft = await self._drafts_repo.get_by_id(draft.id)
        if updated_draft is None:
            raise DraftNotFoundException()
        updated_draft.hashtags = hashtags
        return updated_draft
