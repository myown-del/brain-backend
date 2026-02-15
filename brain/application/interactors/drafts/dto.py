from dataclasses import dataclass
from uuid import UUID

from brain.application.types import Unset, UnsetType


@dataclass
class CreateDraft:
    user_id: UUID
    text: str | None = None
    file_id: UUID | None = None


@dataclass
class UpdateDraft:
    draft_id: UUID
    text: str | None | UnsetType = Unset
    file_id: UUID | None | UnsetType = Unset
    patch: str | None | UnsetType = Unset
