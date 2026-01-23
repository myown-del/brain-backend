from uuid import UUID, uuid4

from brain.application.abstractions.repositories.notes import INotesRepository
from brain.application.abstractions.repositories.notes_graph import (
    INotesGraphRepository,
)
from brain.application.interactors.notes.dto import CreateNote
from brain.application.interactors.users.get_user import GetUserInteractor
from brain.application.services.keyword_notes import KeywordNoteService
from brain.application.services.note_titles import NoteTitleService
from brain.application.services.note_keyword_sync import NoteKeywordSyncService
from brain.domain.entities.note import Note


class CreateNoteInteractor:
    def __init__(
        self,
        get_user_interactor: GetUserInteractor,
        notes_repo: INotesRepository,
        notes_graph_repo: INotesGraphRepository,
        keyword_note_service: KeywordNoteService,
        note_title_service: NoteTitleService,
        keyword_sync_service: NoteKeywordSyncService,
    ):
        self._get_user_interactor = get_user_interactor
        self._notes_repo = notes_repo
        self._notes_graph_repo = notes_graph_repo
        self._keyword_note_service = keyword_note_service
        self._note_title_service = note_title_service
        self._keyword_sync_service = keyword_sync_service

    async def create_note(self, note_data: CreateNote) -> UUID:
        user = await self._get_user_interactor.get_user_by_telegram_id(note_data.by_user_telegram_id)

        title = await self._note_title_service.resolve_create_title(
            user_id=user.id,
            title=note_data.title,
        )
        represents_keyword_id = await self._keyword_note_service.ensure_keyword_for_title(
            user_id=user.id,
            title=title,
        )
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
