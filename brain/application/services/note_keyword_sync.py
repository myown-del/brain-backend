from brain.application.abstractions.repositories.keywords import IKeywordsRepository
from brain.application.abstractions.repositories.notes_graph import (
    INotesGraphRepository,
)
from brain.domain.entities.note import Note
from brain.domain.services.wikilinks import extract_link_targets


class NoteKeywordSyncService:
    def __init__(
        self,
        keywords_repo: IKeywordsRepository,
        notes_graph_repo: INotesGraphRepository,
    ):
        self._keywords_repo = keywords_repo
        self._notes_graph_repo = notes_graph_repo

    async def sync(
        self,
        note: Note,
        previous_state: Note | None = None,
    ) -> None:
        current_targets = extract_link_targets(note.text or "")

        await self._keywords_repo.replace_note_keywords(
            note_id=note.id,
            user_id=note.user_id,
            names=current_targets,
        )

        await self._notes_graph_repo.sync_connections(
            note=note,
            link_targets=current_targets,
            previous_title=previous_state.title if previous_state else None,
            previous_represents_keyword_id=(previous_state.represents_keyword_id if previous_state else None),
        )
