from uuid import uuid4
from unittest.mock import AsyncMock

import pytest

from brain.application.interactors.drafts.exceptions import DraftNotFoundException
from brain.application.services.draft_access import DraftDeletionService


@pytest.mark.asyncio
async def test_delete_draft_removes_existing_entity():
    repo = AsyncMock()
    repo.get_by_id.return_value = object()
    service = DraftDeletionService(repo)
    draft_id = uuid4()

    await service.delete_draft(draft_id)

    repo.delete_by_id.assert_called_once_with(draft_id)


@pytest.mark.asyncio
async def test_delete_draft_raises_if_missing():
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    service = DraftDeletionService(repo)

    with pytest.raises(DraftNotFoundException):
        await service.delete_draft(uuid4())
