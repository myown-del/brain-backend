from dataclasses import dataclass
from uuid import UUID
from brain.application.types import Unset, UnsetType


@dataclass
class CreateNote:
    by_user_telegram_id: int
    title: str | None
    text: str | None


@dataclass
class UpdateNote:
    note_id: UUID
    title: str | None | UnsetType = Unset
    text: str | None | UnsetType = Unset
    patch: str | None | UnsetType = Unset
    is_pinned: bool | UnsetType = Unset
