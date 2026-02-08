from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, model_validator


class ReadNoteSchema(BaseModel):
    id: UUID
    title: str
    text: str | None
    is_pinned: bool
    created_at: datetime
    updated_at: datetime


class CreateNoteSchema(BaseModel):
    title: str | None = None
    text: str | None = None


class UpdateNoteSchema(BaseModel):
    title: str | None = None
    text: str | None = None
    patch: str | None = None
    is_pinned: bool | None = None


class WikilinkSuggestionSchema(BaseModel):
    title: str
    represents_keyword: bool


class NoteCreationStatSchema(BaseModel):
    date: date
    count: int


class NewNoteTitleSchema(BaseModel):
    title: str
