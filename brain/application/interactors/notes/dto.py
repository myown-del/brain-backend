from dataclasses import dataclass
from uuid import UUID
from brain.application.types import Unset, UnsetType


@dataclass
class CreateNote:
    by_user_telegram_id: int
    title: str | None
    text: str | None


@dataclass
class CreateNoteFromDraft:
    by_user_telegram_id: int
    draft_id: UUID
    title: str | None


@dataclass
class UpdateNote:
    note_id: UUID
    title: str | None | UnsetType = Unset
    text: str | None | UnsetType = Unset
    patch: str | None | UnsetType = Unset
    is_pinned: bool | UnsetType = Unset
    is_archived: bool | UnsetType = Unset


@dataclass
class MergeNotes:
    by_user_telegram_id: int
    source_note_ids: list[UUID]
    target_note_id: UUID


@dataclass
class AppendNoteFromDraft:
    by_user_telegram_id: int
    note_id: UUID
    draft_id: UUID
