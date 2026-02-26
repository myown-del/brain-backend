from datetime import datetime

from brain.application.abstractions.repositories.notes import INotesRepository
from brain.domain.entities.note import Note


class GetNotesInteractor:
    def __init__(self, notes_repo: INotesRepository):
        self._notes_repo = notes_repo

    async def get_notes(
        self,
        user_telegram_id: int,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        pinned_first: bool = True,
        include_archived: bool = False,
    ) -> list[Note]:
        return await self._notes_repo.get_by_user_telegram_id(
            user_telegram_id,
            from_date=from_date,
            to_date=to_date,
            pinned_first=pinned_first,
            include_archived=include_archived,
        )
