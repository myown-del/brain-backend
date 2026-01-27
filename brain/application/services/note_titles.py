from uuid import UUID

from brain.application.abstractions.repositories.notes import INotesRepository
from brain.application.interactors.notes.exceptions import (
    NoteTitleAlreadyExistsException,
    NoteTitleRequiredException,
)


class NoteTitleService:
    def __init__(self, notes_repo: INotesRepository):
        self._notes_repo = notes_repo

    async def resolve_create_title(self, user_id: UUID, title: str | None) -> str:
        if title is None:
            title = await self._next_untitled(user_id)
        await self.ensure_unique_title(user_id, title)
        return title

    async def ensure_update_title(
        self,
        user_id: UUID,
        title: str | None,
        exclude_note_id: UUID | None = None,
    ) -> str:
        if title is None:
            raise NoteTitleRequiredException()
        await self.ensure_unique_title(
            user_id=user_id,
            title=title,
            exclude_note_id=exclude_note_id,
        )
        return title

    async def ensure_unique_title(
        self,
        user_id: UUID,
        title: str,
        exclude_note_id: UUID | None = None,
    ) -> None:
        existing_count = await self._notes_repo.count_notes_by_user_and_title(
            user_id=user_id,
            title=title,
            exclude_note_id=exclude_note_id,
        )
        if existing_count > 0:
            raise NoteTitleAlreadyExistsException()

    async def get_next_untitled_title(self, user_id: UUID) -> str:
        return await self._next_untitled(user_id)

    async def _next_untitled(self, user_id: UUID) -> str:
        index = 1
        while True:
            candidate = f"Untitled {index}"
            existing_count = await self._notes_repo.count_notes_by_user_and_title(
                user_id=user_id,
                title=candidate,
            )
            if existing_count == 0:
                return candidate
            index += 1
