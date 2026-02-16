from uuid import uuid4

import pytest
from starlette import status

from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.notes.helpers import create_keyword_note


@pytest.mark.asyncio
async def test_get_note_success(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    note = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Read Me",
        text="Note text",
    )

    async with api_client(notes_app) as client:
        response = await client.request(
            method="GET",
            url=f"/api/notes/{note.id}",
        )

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["id"] == str(note.id)
    assert payload["title"] == "Read Me"
    assert payload["text"] == "Note text"


@pytest.mark.asyncio
async def test_get_note_not_found(notes_app, api_client):
    note_id = uuid4()

    async with api_client(notes_app) as client:
        response = await client.request(
            method="GET",
            url=f"/api/notes/{note_id}",
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Note not found"


@pytest.mark.asyncio
async def test_get_note_forbidden(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    other_user = User(
        id=uuid4(),
        telegram_id=987654,
        username="other",
        first_name="Other",
        last_name="User",
    )
    await repo_hub.users.create(entity=other_user)
    note = await create_keyword_note(
        repo_hub=repo_hub,
        user=other_user,
        title="Private Note",
        text="Private text",
    )

    async with api_client(notes_app) as client:
        response = await client.request(
            method="GET",
            url=f"/api/notes/{note.id}",
        )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Forbidden"
