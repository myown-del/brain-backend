from uuid import uuid4
from unittest.mock import AsyncMock

import pytest

from brain.application.services.note_lookup import NoteLookupService


@pytest.mark.asyncio
async def test_get_note_by_id_delegates_to_repo():
    repo = AsyncMock()
    note = object()
    note_id = uuid4()
    repo.get_by_id.return_value = note
    service = NoteLookupService(repo)

    result = await service.get_note_by_id(note_id)

    assert result is note
    repo.get_by_id.assert_called_once_with(note_id)


@pytest.mark.asyncio
async def test_get_note_by_title_delegates_to_repo():
    repo = AsyncMock()
    note = object()
    user_id = uuid4()
    repo.get_by_title.return_value = note
    service = NoteLookupService(repo)

    result = await service.get_note_by_title(user_id, "title", True)

    assert result is note
    repo.get_by_title.assert_called_once_with(user_id, "title", True)
