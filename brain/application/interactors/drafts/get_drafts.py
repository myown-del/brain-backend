from datetime import datetime
from uuid import UUID

from brain.application.abstractions.repositories.drafts import IDraftsRepository
from brain.domain.entities.draft import Draft
from brain.domain.services.hashtags import normalize_hashtag_texts


class GetDraftsInteractor:
    def __init__(self, drafts_repo: IDraftsRepository):
        self._drafts_repo = drafts_repo

    async def get_drafts(
        self,
        user_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        hashtags: list[str] | None = None,
    ) -> list[Draft]:
        normalized_hashtags = normalize_hashtag_texts(hashtags or [])
        return await self._drafts_repo.get_by_user(
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
            hashtags=normalized_hashtags or None,
        )
