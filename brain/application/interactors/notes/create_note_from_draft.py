from uuid import UUID

from brain.application.abstractions.repositories.drafts import IDraftsRepository
from brain.application.interactors.drafts.exceptions import DraftNotFoundException
from brain.application.interactors.notes.create_note import CreateNoteInteractor
from brain.application.interactors.notes.dto import CreateNote, CreateNoteFromDraft
from brain.application.interactors.users.get_user import GetUserInteractor


class DraftForbiddenException(Exception):
    pass


class CreateNoteFromDraftInteractor:
    def __init__(
        self,
        get_user_interactor: GetUserInteractor,
        drafts_repo: IDraftsRepository,
        create_note_interactor: CreateNoteInteractor,
    ):
        self._get_user_interactor = get_user_interactor
        self._drafts_repo = drafts_repo
        self._create_note_interactor = create_note_interactor

    async def create_note_from_draft(self, note_data: CreateNoteFromDraft) -> UUID:
        user = await self._get_user_interactor.get_user_by_telegram_id(note_data.by_user_telegram_id)
        draft = await self._drafts_repo.get_by_id(note_data.draft_id)
        if draft is None:
            raise DraftNotFoundException()
        if draft.user_id != user.id:
            raise DraftForbiddenException()

        await self._drafts_repo.delete_by_id(draft.id)
        return await self._create_note_interactor.create_note(
            CreateNote(
                by_user_telegram_id=note_data.by_user_telegram_id,
                title=note_data.title,
                text=draft.text,
            ),
        )
