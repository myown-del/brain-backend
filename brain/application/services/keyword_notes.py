from uuid import UUID

from brain.application.abstractions.repositories.keywords import IKeywordsRepository
from brain.application.interactors.notes.exceptions import (
    KeywordNotFoundException,
)


class KeywordNoteService:
    def __init__(
        self,
        keywords_repo: IKeywordsRepository,
    ):
        self._keywords_repo = keywords_repo

    async def ensure_keyword_for_title(
        self,
        user_id: UUID,
        title: str,
    ) -> UUID:
        keyword = await self._keywords_repo.get_by_user_and_name(user_id, name=title)
        if not keyword:
            await self._keywords_repo.ensure_keywords(user_id=user_id, names=[title])
            keyword = await self._keywords_repo.get_by_user_and_name(user_id, name=title)

        if not keyword:
            raise KeywordNotFoundException()

        return keyword.id
