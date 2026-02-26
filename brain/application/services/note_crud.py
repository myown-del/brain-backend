from uuid import UUID, uuid4

from brain.application.abstractions.repositories.keywords import IKeywordsRepository
from brain.application.abstractions.repositories.notes import INotesRepository
from brain.application.abstractions.repositories.notes_graph import INotesGraphRepository
from brain.application.interactors.notes.dto import CreateNote, UpdateNote
from brain.application.interactors.notes.exceptions import NoteNotFoundException
from brain.application.services.keyword_notes import KeywordNoteService
from brain.application.services.note_keyword_sync import NoteKeywordSyncService
from brain.application.services.note_titles import NoteTitleService
from brain.application.services.user_lookup import UserLookupService
from brain.application.types import Unset
from brain.domain.entities.note import Note
from brain.domain.services.diffs import apply_patch, check_if_ranges_touched, get_diffs
from brain.domain.services.keywords import collect_cleanup_keyword_names
from brain.domain.services.wikilinks import extract_link_intervals, extract_link_targets
from brain.domain.time import utc_now


class NoteCreationService:
    def __init__(
        self,
        user_lookup_service: UserLookupService,
        notes_repo: INotesRepository,
        notes_graph_repo: INotesGraphRepository,
        keyword_note_service: KeywordNoteService,
        note_title_service: NoteTitleService,
        keyword_sync_service: NoteKeywordSyncService,
    ):
        self._user_lookup_service = user_lookup_service
        self._notes_repo = notes_repo
        self._notes_graph_repo = notes_graph_repo
        self._keyword_note_service = keyword_note_service
        self._note_title_service = note_title_service
        self._keyword_sync_service = keyword_sync_service

    async def create_note(self, note_data: CreateNote) -> UUID:
        user = await self._user_lookup_service.get_user_by_telegram_id(note_data.by_user_telegram_id)
        title = await self._note_title_service.resolve_create_title(user_id=user.id, title=note_data.title)
        represents_keyword_id = await self._keyword_note_service.ensure_keyword_for_title(user_id=user.id, title=title)

        note = Note(
            id=uuid4(),
            user_id=user.id,
            title=title,
            text=note_data.text,
            represents_keyword_id=represents_keyword_id,
        )
        await self._notes_repo.create(note)
        await self._notes_graph_repo.upsert_note(note)
        await self._keyword_sync_service.sync(note)
        return note.id


class NoteUpdateService:
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
            is_archived=note.is_archived,
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

        if note_data.patch and note_data.patch is not Unset:
            try:
                note.text = apply_patch(note.text or "", note_data.patch)
            except Exception:
                raise ValueError("Failed to apply patch")
        elif note_data.text is not Unset:
            note.text = note_data.text

        if note_data.is_pinned is not Unset:
            note.is_pinned = note_data.is_pinned
        if note_data.is_archived is not Unset:
            note.is_archived = note_data.is_archived

        should_sync_graph = True
        if note.link_intervals and note_data.patch and note_data.patch is not Unset:
            diffs = get_diffs(previous_state.text or "", note.text or "")
            touched_old = check_if_ranges_touched(
                old_text_len=len(previous_state.text or ""),
                diffs=diffs,
                protected_ranges=previous_state.link_intervals,
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
        removed_targets = [title for title in previous_cleanup_names if title not in set(current_cleanup_names)]
        await self._keywords_repo.delete_unused_keywords(user_id=note.user_id, names=removed_targets)

        return note


class NoteDeletionService:
    def __init__(
        self,
        notes_repo: INotesRepository,
        keywords_repo: IKeywordsRepository,
        notes_graph_repo: INotesGraphRepository,
    ):
        self._notes_repo = notes_repo
        self._keywords_repo = keywords_repo
        self._notes_graph_repo = notes_graph_repo

    async def delete_note(self, note_id: UUID) -> None:
        note = await self._notes_repo.get_by_id(note_id)
        if note is None:
            raise NoteNotFoundException()

        link_targets = await self._keywords_repo.get_note_keyword_names(note_id)
        cleanup_names = collect_cleanup_keyword_names(
            link_targets=link_targets,
            represents_keyword_id=note.represents_keyword_id,
            title=note.title,
        )
        await self._notes_repo.delete_by_id(note_id)
        await self._keywords_repo.delete_note_keywords(note_id)
        await self._keywords_repo.delete_unused_keywords(user_id=note.user_id, names=cleanup_names)
        await self._notes_graph_repo.delete_note(note_id)
