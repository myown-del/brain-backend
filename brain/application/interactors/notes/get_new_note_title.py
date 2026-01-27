from uuid import UUID

from brain.application.services.note_titles import NoteTitleService


class GetNewNoteTitleInteractor:
    def __init__(self, note_title_service: NoteTitleService):
        self._note_title_service = note_title_service

    async def get_title(self, user_id: UUID) -> str:
        return await self._note_title_service.get_next_untitled_title(user_id)
