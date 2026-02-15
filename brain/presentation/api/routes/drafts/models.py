from datetime import datetime
from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from brain.presentation.api.routes.users.models import ReadS3FileSchema


class ReadDraftSchema(BaseModel):
    id: UUID
    text: str | None
    file: ReadS3FileSchema | None
    hashtags: list[str]
    created_at: datetime
    updated_at: datetime


class CreateDraftSchema(BaseModel):
    text: str | None = None
    file_id: UUID | None = None


class UpdateDraftSchema(BaseModel):
    text: str | None = None
    file_id: UUID | None = None
    patch: str | None = None


class SearchDraftsSchema(BaseModel):
    text_query: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    hashtags: list[str] = Field(default_factory=list)


class DraftCreationStatSchema(BaseModel):
    date: date
    count: int
