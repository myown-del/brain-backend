from dataclasses import dataclass
from uuid import UUID

from brain.application.types import Unset, UnsetType


@dataclass
class CreateDraft:
    user_id: UUID
    text: str | None = None


@dataclass
class UpdateDraft:
    draft_id: UUID
    text: str | None | UnsetType = Unset
    patch: str | None | UnsetType = Unset
