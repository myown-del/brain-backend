from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReadS3FileSchema(BaseModel):
    id: UUID
    object_name: str
    url: str
    content_type: str | None
    created_at: datetime | None
    updated_at: datetime | None


class ReadUserSchema(BaseModel):
    id: UUID
    telegram_id: int
    username: str | None
    first_name: str
    last_name: str | None
    profile_picture: ReadS3FileSchema | None
    created_at: datetime
    updated_at: datetime
