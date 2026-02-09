from dataclasses import dataclass, field
from datetime import datetime

from brain.domain.entities.common import Entity


@dataclass
class Hashtag(Entity):
    """
    Hashtag referenced by drafts.
    """

    text: str
    created_at: datetime | None = field(default=None, kw_only=True)
