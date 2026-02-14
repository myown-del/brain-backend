from uuid import UUID

from brain.application.abstractions.repositories.drafts import IDraftsRepository
from brain.application.abstractions.repositories.models import DraftCreationStat


class GetDraftCreationStatsInteractor:
    def __init__(self, drafts_repo: IDraftsRepository):
        self._drafts_repo = drafts_repo

    async def get_stats(
        self,
        user_id: UUID,
        timezone_name: str = "UTC",
    ) -> list[DraftCreationStat]:
        return await self._drafts_repo.get_draft_creation_stats_by_user_id(
            user_id=user_id,
            timezone_name=timezone_name,
        )
