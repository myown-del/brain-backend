from uuid import UUID

from brain.application.interactors.notes.dto import MergeNotes, UpdateNote
from brain.application.interactors.notes.exceptions import NoteNotFoundException
from brain.application.services.note_crud import NoteDeletionService, NoteUpdateService
from brain.application.services.note_lookup import NoteLookupService
from brain.application.services.user_lookup import UserLookupService
from brain.domain.entities.note import Note
from brain.domain.services.note_text import NoteTextService


class MergeNotesForbiddenException(Exception):
    pass


class MergeNotesValidationException(Exception):
    pass


class MergeNotesInteractor:
    def __init__(
        self,
        user_lookup_service: UserLookupService,
        note_lookup_service: NoteLookupService,
        note_update_service: NoteUpdateService,
        note_deletion_service: NoteDeletionService,
        note_text_service: NoteTextService,
    ):
        self._user_lookup_service = user_lookup_service
        self._note_lookup_service = note_lookup_service
        self._note_update_service = note_update_service
        self._note_deletion_service = note_deletion_service
        self._note_text_service = note_text_service

    async def _get_note_or_raise(self, note_id: UUID) -> Note:
        note = await self._note_lookup_service.get_note_by_id(note_id)
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

        user = await self._user_lookup_service.get_user_by_telegram_id(data.by_user_telegram_id)
        source_notes = [await self._get_note_or_raise(note_id) for note_id in data.source_note_ids]
        target_note = await self._get_note_or_raise(data.target_note_id)

        notes_to_validate = source_notes + [target_note]
        if any(note.user_id != user.id for note in notes_to_validate):
            raise MergeNotesForbiddenException()

        source_text = self._note_text_service.chain_with_newline([note.text for note in source_notes])

        updated_target = target_note
        if source_text is not None:
            text = self._note_text_service.append_with_newline(target_note.text, source_text)
            updated_target = await self._note_update_service.update_note(
                UpdateNote(note_id=target_note.id, text=text),
            )

        for source_note in source_notes:
            await self._note_deletion_service.delete_note(source_note.id)
        return updated_target
