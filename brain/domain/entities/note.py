from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from brain.domain.entities.common import Entity
from brain.domain.value_objects import LinkInterval


@dataclass
class Note(Entity):
    """
    Note domain model
    """

    id: UUID | None = field(default=None, kw_only=True)
    user_id: UUID
    title: str
    text: str | None = field(default=None, kw_only=True)
    represents_keyword_id: UUID
    is_pinned: bool = field(default=False, kw_only=True)
    updated_at: datetime | None = field(default=None, kw_only=True)
    created_at: datetime | None = field(default=None, kw_only=True)
    link_intervals: list[LinkInterval] = field(default_factory=list, kw_only=True)
