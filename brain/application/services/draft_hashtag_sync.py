from uuid import UUID

from brain.application.abstractions.repositories.hashtags import IHashtagsRepository
from brain.domain.services.hashtags import extract_hashtags


class DraftHashtagSyncService:
    def __init__(self, hashtags_repo: IHashtagsRepository):
        self._hashtags_repo = hashtags_repo

    async def sync(
        self,
        draft_id: UUID,
        text: str | None,
    ) -> list[str]:
        hashtags = extract_hashtags(text)
        await self._hashtags_repo.replace_draft_hashtags(
            draft_id=draft_id,
            texts=hashtags,
        )
        return hashtags
