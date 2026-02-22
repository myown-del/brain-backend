from brain.application.interactors.drafts.exceptions import DraftNotFoundException
from brain.application.interactors.notes.dto import AppendNoteFromDraft, UpdateNote
from brain.application.interactors.notes.exceptions import NoteNotFoundException
from brain.application.abstractions.uow import UnitOfWorkFactory
from brain.application.services.draft_access import DraftDeletionService, DraftLookupService
from brain.application.services.note_crud import NoteUpdateService
from brain.application.services.note_lookup import NoteLookupService
from brain.application.services.user_lookup import UserLookupService
from brain.domain.entities.note import Note
from brain.domain.services.note_text import NoteTextService


class AppendFromDraftForbiddenException(Exception):
    pass


class AppendNoteFromDraftInteractor:
    def __init__(
        self,
        user_lookup_service: UserLookupService,
        note_lookup_service: NoteLookupService,
        draft_lookup_service: DraftLookupService,
        note_update_service: NoteUpdateService,
        draft_deletion_service: DraftDeletionService,
        note_text_service: NoteTextService,
        uow_factory: UnitOfWorkFactory,
    ):
        self._user_lookup_service = user_lookup_service
        self._note_lookup_service = note_lookup_service
        self._draft_lookup_service = draft_lookup_service
        self._note_update_service = note_update_service
        self._draft_deletion_service = draft_deletion_service
        self._note_text_service = note_text_service
        self._uow_factory = uow_factory

    async def append_from_draft(self, data: AppendNoteFromDraft) -> Note:
        async with self._uow_factory() as uow:
            user = await self._user_lookup_service.get_user_by_telegram_id(data.by_user_telegram_id)
            note = await self._note_lookup_service.get_note_by_id(data.note_id)
            if note is None:
                raise NoteNotFoundException()

            draft = await self._draft_lookup_service.get_draft_by_id(data.draft_id)
            if draft is None:
                raise DraftNotFoundException()

            if note.user_id != user.id or draft.user_id != user.id:
                raise AppendFromDraftForbiddenException()

            text = self._note_text_service.append_with_newline(note.text, draft.text)
            updated_note = note
            if text != note.text:
                updated_note = await self._note_update_service.update_note(
                    UpdateNote(note_id=note.id, text=text),
                )
            await self._draft_deletion_service.delete_draft(draft.id)
            await uow.commit()
            return updated_note
