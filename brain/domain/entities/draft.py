from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from brain.domain.entities.common import Entity
from brain.domain.entities.s3_file import S3File


@dataclass
class Draft(Entity):
    """
    Draft domain model.
    """

    id: UUID | None = field(default=None, kw_only=True)
    user_id: UUID
    text: str | None = field(default=None, kw_only=True)
    file_id: UUID | None = field(default=None, kw_only=True)
    file: S3File | None = field(default=None, kw_only=True)
    hashtags: list[str] = field(default_factory=list, kw_only=True)
    updated_at: datetime | None = field(default=None, kw_only=True)
    created_at: datetime | None = field(default=None, kw_only=True)
