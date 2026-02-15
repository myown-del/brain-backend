from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ReadFileOutput:
    id: UUID
    name: str
    path: str
    content_type: str
    created_at: datetime | None
    url: str
