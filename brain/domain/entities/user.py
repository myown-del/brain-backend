from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from brain.domain.entities.common import Entity
from brain.domain.entities.s3_file import S3File


@dataclass
class User(Entity):
    """
    User domain model
    """

    id: UUID | None = field(default=None, kw_only=True)
    telegram_id: int
    username: str | None = field(default=None, kw_only=True)
    first_name: str
    last_name: str | None = field(default=None, kw_only=True)
    profile_picture_file_id: UUID | None = field(default=None, kw_only=True)
    pin_hash: str | None = field(default=None, kw_only=True)
    profile_picture: S3File | None = field(default=None, kw_only=True)
    created_at: datetime | None = field(default=None, kw_only=True)
    updated_at: datetime | None = field(default=None, kw_only=True)
