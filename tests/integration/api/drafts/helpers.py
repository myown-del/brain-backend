from datetime import datetime
from uuid import UUID, uuid4

from brain.domain.entities.draft import Draft
from brain.domain.entities.user import User
from brain.domain.services.hashtags import normalize_hashtag_texts
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.utils.uow import commit_repo_hub


async def create_draft(
    repo_hub: RepositoryHub,
    user: User,
    text: str | None = None,
    file_id: UUID | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    hashtags: list[str] | None = None,
) -> Draft:
    draft = Draft(
        id=uuid4(),
        user_id=user.id,
        text=text,
        file_id=file_id,
        created_at=created_at,
        updated_at=updated_at,
    )
    await repo_hub.drafts.create(entity=draft)
    await repo_hub.hashtags.replace_draft_hashtags(
        draft_id=draft.id,
        texts=normalize_hashtag_texts(hashtags or []),
    )
    await commit_repo_hub(repo_hub)
    return draft
