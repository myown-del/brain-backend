from dataclasses import asdict

from uuid import UUID

from brain.application.interactors.notes.dto import (
    CreateNote,
    CreateNoteFromDraft,
    UpdateNote,
)
from brain.domain.entities.note import Note
from brain.domain.entities.user import User
from brain.presentation.api.routes.notes.models import (
    CreateNoteSchema,
    CreateNoteFromDraftSchema,
    ReadNoteSchema,
    UpdateNoteSchema,
    WikilinkSuggestionSchema,
    NoteCreationStatSchema,
)
from brain.application.abstractions.repositories.models import (
    WikilinkSuggestion,
    NoteCreationStat,
)
from brain.application.types import Unset


def map_note_to_read_schema(note: Note) -> ReadNoteSchema:
    payload = asdict(note)
    payload.pop("represents_keyword_id", None)
    return ReadNoteSchema.model_validate(payload)


def map_create_schema_to_dto(
    schema: CreateNoteSchema,
    user: User,
) -> CreateNote:
    return CreateNote(
        by_user_telegram_id=user.telegram_id,
        title=schema.title,
        text=schema.text,
    )


def map_update_schema_to_dto(
    note_id: UUID,
    schema: UpdateNoteSchema,
) -> UpdateNote:
    payload = schema.model_dump(exclude_unset=True)
    return UpdateNote(
        note_id=note_id,
        title=payload.get("title", Unset),
        text=payload.get("text", Unset),
        patch=payload.get("patch", Unset),
        is_pinned=payload.get("is_pinned", Unset),
    )


def map_create_from_draft_schema_to_dto(
    schema: CreateNoteFromDraftSchema,
    user: User,
) -> CreateNoteFromDraft:
    return CreateNoteFromDraft(
        by_user_telegram_id=user.telegram_id,
        draft_id=schema.draft_id,
        title=schema.title,
    )


def map_wikilink_suggestion_to_schema(
    suggestion: WikilinkSuggestion,
) -> WikilinkSuggestionSchema:
    return WikilinkSuggestionSchema.model_validate(asdict(suggestion))


def map_note_creation_stat_to_schema(
    stat: NoteCreationStat,
) -> NoteCreationStatSchema:
    return NoteCreationStatSchema.model_validate(asdict(stat))
