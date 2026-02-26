from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReadNoteSchema(BaseModel):
    id: UUID
    title: str
    text: str | None
    is_pinned: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class CreateNoteSchema(BaseModel):
    title: str | None = None
    text: str | None = None


class CreateNoteFromDraftSchema(BaseModel):
    draft_id: UUID
    title: str | None = None


class UpdateNoteSchema(BaseModel):
    title: str | None = None
    text: str | None = None
    patch: str | None = None
    is_pinned: bool | None = None
    is_archived: bool | None = None


class WikilinkSuggestionSchema(BaseModel):
    title: str
    represents_keyword: bool


class NoteCreationStatSchema(BaseModel):
    date: date
    count: int


class NewNoteTitleSchema(BaseModel):
    title: str


class MergeNotesSchema(BaseModel):
    source_note_ids: list[UUID] = Field(min_length=1)
    target_note_id: UUID


class AppendFromDraftSchema(BaseModel):
    note_id: UUID
    draft_id: UUID
