from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from brain.domain.entities.common import Entity


@dataclass
class ApiKey(Entity):
    id: UUID
    user_id: UUID
    name: str
    key_hash: str
    created_at: datetime | None = field(default=None, kw_only=True)
