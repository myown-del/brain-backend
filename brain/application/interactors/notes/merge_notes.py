from uuid import UUID

from brain.application.interactors.notes.delete_note import DeleteNoteInteractor
from brain.application.interactors.notes.dto import MergeNotes, UpdateNote
from brain.application.interactors.notes.exceptions import NoteNotFoundException
from brain.application.interactors.notes.get_note import GetNoteInteractor
from brain.application.interactors.notes.update_note import UpdateNoteInteractor
from brain.application.interactors.users.get_user import GetUserInteractor
from brain.domain.entities.note import Note
from brain.domain.services.note_text import NoteTextService


class MergeNotesForbiddenException(Exception):
    pass


class MergeNotesValidationException(Exception):
    pass


class MergeNotesInteractor:
    def __init__(
        self,
        get_user_interactor: GetUserInteractor,
        get_note_interactor: GetNoteInteractor,
        update_note_interactor: UpdateNoteInteractor,
        delete_note_interactor: DeleteNoteInteractor,
        note_text_service: NoteTextService,
    ):
        self._get_user_interactor = get_user_interactor
        self._get_note_interactor = get_note_interactor
        self._update_note_interactor = update_note_interactor
        self._delete_note_interactor = delete_note_interactor
        self._note_text_service = note_text_service

    async def _get_note_or_raise(self, note_id: UUID) -> Note:
        note = await self._get_note_interactor.get_note_by_id(note_id)
        if note is None:
            raise NoteNotFoundException()
        return note

    async def merge_notes(self, data: MergeNotes) -> Note:
        if not data.source_note_ids:
            raise MergeNotesValidationException("source_note_ids cannot be empty")
        if len(set(data.source_note_ids)) != len(data.source_note_ids):
            raise MergeNotesValidationException("Note ids must be unique")
        if data.target_note_id in set(data.source_note_ids):
            raise MergeNotesValidationException("Source notes cannot include target note")

        user = await self._get_user_interactor.get_user_by_telegram_id(
            data.by_user_telegram_id,
        )
        source_notes = [await self._get_note_or_raise(note_id) for note_id in data.source_note_ids]
        target_note = await self._get_note_or_raise(data.target_note_id)

        notes_to_validate = source_notes + [target_note]
        if any(note.user_id != user.id for note in notes_to_validate):
            raise MergeNotesForbiddenException()

        source_text = self._note_text_service.chain_with_newline(
            [note.text for note in source_notes],
        )

        updated_target = target_note
        if source_text is not None:
            text = self._note_text_service.append_with_newline(target_note.text, source_text)
            updated_target = await self._update_note_interactor.update_note(
                UpdateNote(note_id=target_note.id, text=text),
            )

        for source_note in source_notes:
            await self._delete_note_interactor.delete_note(source_note.id)
        return updated_target
