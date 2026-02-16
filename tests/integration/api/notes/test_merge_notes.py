from uuid import uuid4

import pytest
from starlette import status

from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.notes.helpers import create_keyword_note


@pytest.mark.asyncio
async def test_merge_notes_success(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    source_one = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Source 1",
        text="Source text 1",
    )
    source_two = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Source 2",
        text="Source text 2",
    )
    target = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Target",
        text="Target text",
    )

    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes/merge",
            json={
                "source_note_ids": [str(source_one.id), str(source_two.id)],
                "target_note_id": str(target.id),
            },
        )

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["id"] == str(target.id)
    assert payload["text"] == "Target text\nSource text 1\nSource text 2"

    stored_target = await repo_hub.notes.get_by_id(target.id)
    assert stored_target is not None
    assert stored_target.text == "Target text\nSource text 1\nSource text 2"

    assert await repo_hub.notes.get_by_id(source_one.id) is None
    assert await repo_hub.notes.get_by_id(source_two.id) is None


@pytest.mark.asyncio
async def test_merge_notes_not_found(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    target = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Target",
        text="Target",
    )

    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes/merge",
            json={
                "source_note_ids": [str(uuid4())],
                "target_note_id": str(target.id),
            },
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Note not found"


@pytest.mark.asyncio
async def test_merge_notes_forbidden(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    other_user = User(
        id=uuid4(),
        telegram_id=654321,
        username="other_user",
        first_name="Other",
        last_name="User",
    )
    await repo_hub.users.create(entity=other_user)
    foreign_source = await create_keyword_note(
        repo_hub=repo_hub,
        user=other_user,
        title="Foreign Source",
        text="Private",
    )
    target = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Target",
        text="Target",
    )

    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes/merge",
            json={
                "source_note_ids": [str(foreign_source.id)],
                "target_note_id": str(target.id),
            },
        )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Forbidden"


@pytest.mark.asyncio
async def test_merge_notes_rejects_overlapping_ids(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    note = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Note",
        text="Text",
    )

    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes/merge",
            json={
                "source_note_ids": [str(note.id)],
                "target_note_id": str(note.id),
            },
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Source notes cannot include target note"
