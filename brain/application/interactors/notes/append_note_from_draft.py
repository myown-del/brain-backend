from brain.application.interactors.drafts.delete_draft import DeleteDraftInteractor
from brain.application.interactors.drafts.exceptions import DraftNotFoundException
from brain.application.interactors.drafts.get_draft import GetDraftInteractor
from brain.application.interactors.notes.dto import AppendNoteFromDraft, UpdateNote
from brain.application.interactors.notes.exceptions import NoteNotFoundException
from brain.application.interactors.notes.get_note import GetNoteInteractor
from brain.application.interactors.notes.update_note import UpdateNoteInteractor
from brain.application.interactors.users.get_user import GetUserInteractor
from brain.domain.entities.note import Note
from brain.domain.services.note_text import NoteTextService


class AppendFromDraftForbiddenException(Exception):
    pass


class AppendNoteFromDraftInteractor:
    def __init__(
        self,
        get_user_interactor: GetUserInteractor,
        get_note_interactor: GetNoteInteractor,
        get_draft_interactor: GetDraftInteractor,
        update_note_interactor: UpdateNoteInteractor,
        delete_draft_interactor: DeleteDraftInteractor,
        note_text_service: NoteTextService,
    ):
        self._get_user_interactor = get_user_interactor
        self._get_note_interactor = get_note_interactor
        self._get_draft_interactor = get_draft_interactor
        self._update_note_interactor = update_note_interactor
        self._delete_draft_interactor = delete_draft_interactor
        self._note_text_service = note_text_service

    async def append_from_draft(self, data: AppendNoteFromDraft) -> Note:
        user = await self._get_user_interactor.get_user_by_telegram_id(
            data.by_user_telegram_id,
        )
        note = await self._get_note_interactor.get_note_by_id(data.note_id)
        if note is None:
            raise NoteNotFoundException()
        draft = await self._get_draft_interactor.get_draft_by_id(data.draft_id)
        if draft is None:
            raise DraftNotFoundException()

        if note.user_id != user.id or draft.user_id != user.id:
            raise AppendFromDraftForbiddenException()

        text = self._note_text_service.append_with_newline(note.text, draft.text)
        updated_note = note
        if text != note.text:
            updated_note = await self._update_note_interactor.update_note(
                UpdateNote(note_id=note.id, text=text),
            )
        await self._delete_draft_interactor.delete_draft(draft.id)
        return updated_note
