from brain.application.abstractions.repositories.notes import INotesRepository
from brain.application.abstractions.repositories.models import NoteCreationStat


class GetNoteCreationStatsInteractor:
    def __init__(self, notes_repo: INotesRepository):
        self._notes_repo = notes_repo

    async def get_stats(
        self,
        user_telegram_id: int,
        timezone_name: str = "UTC",
    ) -> list[NoteCreationStat]:
        return await self._notes_repo.get_note_creation_stats_by_user_telegram_id(
            telegram_id=user_telegram_id,
            timezone_name=timezone_name,
        )
