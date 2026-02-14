from datetime import datetime
from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class ReadDraftSchema(BaseModel):
    id: UUID
    text: str | None
    hashtags: list[str]
    created_at: datetime
    updated_at: datetime


class CreateDraftSchema(BaseModel):
    text: str | None = None


class UpdateDraftSchema(BaseModel):
    text: str | None = None
    patch: str | None = None


class SearchDraftsSchema(BaseModel):
    text_query: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    hashtags: list[str] = Field(default_factory=list)


class DraftCreationStatSchema(BaseModel):
    date: date
    count: int
