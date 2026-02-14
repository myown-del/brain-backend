from uuid import UUID

from brain.application.abstractions.repositories.keywords import IKeywordsRepository
from brain.application.abstractions.repositories.notes import INotesRepository
from brain.application.abstractions.repositories.notes_graph import (
    INotesGraphRepository,
)
from brain.application.interactors.notes.dto import UpdateNote
from brain.application.interactors.notes.exceptions import NoteNotFoundException
from brain.application.services.keyword_notes import KeywordNoteService
from brain.application.services.note_titles import NoteTitleService
from brain.application.services.note_keyword_sync import NoteKeywordSyncService
from brain.domain.entities.note import Note
from brain.domain.services.wikilinks import extract_link_targets, extract_link_intervals
from brain.domain.services.diffs import apply_patch, get_diffs, check_if_ranges_touched
from brain.application.types import Unset

from brain.domain.services.keywords import collect_cleanup_keyword_names
from brain.domain.time import utc_now


class UpdateNoteInteractor:
    def __init__(
        self,
        notes_repo: INotesRepository,
        notes_graph_repo: INotesGraphRepository,
        keywords_repo: IKeywordsRepository,
        keyword_note_service: KeywordNoteService,
        note_title_service: NoteTitleService,
        keyword_sync_service: NoteKeywordSyncService,
    ):
        self._notes_repo = notes_repo
        self._notes_graph_repo = notes_graph_repo
        self._keywords_repo = keywords_repo
        self._keyword_note_service = keyword_note_service
        self._note_title_service = note_title_service
        self._keyword_sync_service = keyword_sync_service

    async def update_note(self, note_data: UpdateNote) -> Note:
        note = await self._notes_repo.get_by_id(note_data.note_id)
        if note is None:
            raise NoteNotFoundException()

        previous_state = Note(
            id=note.id,
            user_id=note.user_id,
            title=note.title,
            text=note.text,
            represents_keyword_id=note.represents_keyword_id,
            is_pinned=note.is_pinned,
            updated_at=note.updated_at,
            created_at=note.created_at,
            link_intervals=note.link_intervals,
        )

        if note_data.title is not Unset:
            title = await self._note_title_service.ensure_update_title(
                user_id=note.user_id,
                title=note_data.title,
                exclude_note_id=note.id,
            )
            note.title = title

            note.represents_keyword_id = await self._keyword_note_service.ensure_keyword_for_title(
                user_id=note.user_id,
                title=note.title,
            )

        note.updated_at = utc_now()

        # Apply patch if present
        if note_data.patch and note_data.patch is not Unset:
            try:
                # NOTE: Logic - if patch provided, derive text.
                # For safety, let's say we trust patch if provided.
                current_text = apply_patch(note.text or "", note_data.patch)
                note.text = current_text
            except Exception:
                # Fallback or error? For now let's error if patch fails.
                raise ValueError("Failed to apply patch")
        elif note_data.text is not Unset:
            note.text = note_data.text
        if note_data.is_pinned is not Unset:
            note.is_pinned = note_data.is_pinned

        # Differential Update Optimization
        # Check if we can skip Neo4j sync
        should_sync_graph = True

        # If we have previous link intervals, check if they are safe
        # We need diffs between OLD text and NEW text.

        # If we just derived text from patch, we implicitly have diffs (from patch).
        # But get_diffs uses dmp which is what we want.

        if note.link_intervals and note_data.patch and note_data.patch is not Unset:
            diffs = get_diffs(previous_state.text or "", note.text or "")
            touched_old = check_if_ranges_touched(
                old_text_len=len(previous_state.text or ""),
                diffs=diffs,
                old_link_intervals=previous_state.link_intervals,
            )
            has_new_brackets = any(("[" in text or "]" in text) for op, text in diffs if op == 1)

            if not touched_old and not has_new_brackets:
                should_sync_graph = False

        note.link_intervals = extract_link_intervals(note.text or "")

        await self._notes_repo.update(note)
        await self._notes_graph_repo.upsert_note(note)

        if should_sync_graph:
            await self._keyword_sync_service.sync(note, previous_state=previous_state)

        previous_targets = extract_link_targets(previous_state.text or "")
        current_targets = extract_link_targets(note.text or "")
        previous_cleanup_names = collect_cleanup_keyword_names(
            link_targets=previous_targets,
            represents_keyword_id=previous_state.represents_keyword_id,
            title=previous_state.title,
        )
        current_cleanup_names = collect_cleanup_keyword_names(
            link_targets=current_targets,
            represents_keyword_id=note.represents_keyword_id,
            title=note.title,
        )
        removed_targets = [
            title for title in previous_cleanup_names
            if title not in set(current_cleanup_names)
        ]  # fmt: skip
        await self._keywords_repo.delete_unused_keywords(
            user_id=note.user_id,
            names=removed_targets,
        )

        return note
