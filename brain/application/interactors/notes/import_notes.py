import io
import json
import zipfile
from uuid import UUID, uuid4

from brain.application.abstractions.repositories.notes import INotesRepository
from brain.application.abstractions.repositories.notes_graph import INotesGraphRepository
from brain.application.interactors.notes.exceptions import NoteTitleAlreadyExistsException
from brain.application.services.keyword_notes import KeywordNoteService
from brain.application.services.note_keyword_sync import NoteKeywordSyncService
from brain.application.services.note_titles import NoteTitleService
from brain.application.services.user_lookup import UserLookupService
from brain.domain.entities.note import Note
from brain.domain.time import parse_iso_datetime


class ImportNotesInteractor:
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

    async def import_notes(self, user_telegram_id: int, zip_bytes: bytes) -> None:
        user = await self._user_lookup_service.get_user_by_telegram_id(user_telegram_id)

        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zip_file:
                for filename in zip_file.namelist():
                    if not filename.endswith(".json"):
                        continue

                    with zip_file.open(filename) as f:
                        try:
                            note_data = json.load(f)
                            await self._import_single_note(user.id, note_data)
                        except Exception:
                            continue
        except zipfile.BadZipFile:
            raise ValueError("Invalid zip file")

    async def _import_single_note(self, user_id: UUID, note_data: dict) -> None:
        title = note_data.get("title")
        text = note_data.get("text")
        is_pinned = bool(note_data.get("is_pinned", False))

        if not title:
            return

        try:
            await self._note_title_service.ensure_unique_title(user_id, title)
        except NoteTitleAlreadyExistsException:
            return

        represents_keyword_id = await self._keyword_note_service.ensure_keyword_for_title(
            user_id=user_id,
            title=title,
        )

        created_at = None
        if note_data.get("created_at"):
            try:
                created_at = parse_iso_datetime(note_data["created_at"])
            except ValueError:
                pass

        updated_at = None
        if note_data.get("updated_at"):
            try:
                updated_at = parse_iso_datetime(note_data["updated_at"])
            except ValueError:
                pass

        note = Note(
            id=uuid4(),
            user_id=user_id,
            title=title,
            text=text,
            represents_keyword_id=represents_keyword_id,
            is_pinned=is_pinned,
            created_at=created_at,
            updated_at=updated_at,
        )

        await self._notes_repo.create(note)
        await self._notes_graph_repo.upsert_note(note)
        await self._keyword_sync_service.sync(note)
