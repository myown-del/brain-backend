from datetime import datetime
from uuid import UUID

from brain.application.abstractions.repositories.drafts import IDraftsRepository
from brain.domain.entities.draft import Draft
from brain.domain.services.hashtags import normalize_hashtag_texts


class SearchDraftsByTextInteractor:
    def __init__(self, drafts_repo: IDraftsRepository):
        self._drafts_repo = drafts_repo

    async def search(
        self,
        user_id: UUID,
        query: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        hashtags: list[str] | None = None,
    ) -> list[Draft]:
        normalized_query = (query or "").strip()
        if not normalized_query:
            return []
        normalized_hashtags = normalize_hashtag_texts(hashtags or [])
        return await self._drafts_repo.search_by_text(
            user_id=user_id,
            query=normalized_query,
            from_date=from_date,
            to_date=to_date,
            hashtags=normalized_hashtags or None,
        )
