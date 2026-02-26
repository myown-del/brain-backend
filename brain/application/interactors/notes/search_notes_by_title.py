from uuid import UUID

from brain.application.abstractions.repositories.notes import INotesRepository
from brain.domain.entities.note import Note


class SearchNotesByTitleInteractor:
    def __init__(self, notes_repo: INotesRepository):
        self._notes_repo = notes_repo

    async def search(
        self,
        user_id: UUID,
        query: str,
        exact_match: bool = False,
        pinned_first: bool = True,
        include_archived: bool = False,
    ) -> list[Note]:
        raw_query = query or ""
        normalized_query = raw_query if exact_match else raw_query.strip()
        if not normalized_query:
            return []

        return await self._notes_repo.search_by_title(
            user_id=user_id,
            query=normalized_query,
            exact_match=exact_match,
            pinned_first=pinned_first,
            include_archived=include_archived,
        )
