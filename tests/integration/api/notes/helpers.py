from datetime import datetime
from uuid import uuid4

from brain.domain.entities.note import Note
from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.utils.uow import commit_repo_hub


async def create_keyword_note(
    repo_hub: RepositoryHub,
    user: User,
    title: str,
    text: str | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    is_pinned: bool = False,
) -> Note:
    await repo_hub.keywords.ensure_keywords(user_id=user.id, names=[title])
    keyword = await repo_hub.keywords.get_by_user_and_name(
        user_id=user.id,
        name=title,
    )
    note = Note(
        id=uuid4(),
        user_id=user.id,
        title=title,
        text=text,
        represents_keyword_id=keyword.id,
        is_pinned=is_pinned,
        created_at=created_at,
        updated_at=updated_at,
    )
    await repo_hub.notes.create(note)
    await commit_repo_hub(repo_hub)
    return note
