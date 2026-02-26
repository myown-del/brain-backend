import pytest
from starlette import status

from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.notes.helpers import create_keyword_note


@pytest.mark.asyncio
async def test_create_note_success(notes_app, api_client, repo_hub: RepositoryHub, user):
    # setup: ensure user exists in db
    note_payload = {"title": "New Note", "text": "Body"}

    # action: create note via API
    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes",
            json=note_payload,
        )

    # check: response and stored note match
    assert response.status_code == status.HTTP_201_CREATED
    payload = response.json()
    assert payload["title"] == "New Note"
    assert payload["text"] == "Body"
    assert payload["is_archived"] is False
    stored = await repo_hub.notes.get_by_title(
        user_id=user.id,
        title="New Note",
        exact_match=True,
    )
    assert stored is not None
    assert payload["id"] == str(stored.id)
    assert stored.is_archived is False


@pytest.mark.asyncio
async def test_create_note_generates_untitled(notes_app, api_client, repo_hub: RepositoryHub, user):
    # setup: no existing notes for user
    note_payload = {"title": None, "text": "Body"}

    # action: create note without title
    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes",
            json=note_payload,
        )

    # check: response uses generated title and note stored
    assert response.status_code == status.HTTP_201_CREATED
    payload = response.json()
    assert payload["title"] == "Untitled 1"
    assert payload["is_archived"] is False
    stored = await repo_hub.notes.get_by_title(
        user_id=user.id,
        title="Untitled 1",
        exact_match=True,
    )
    assert stored is not None
    assert stored.is_archived is False


@pytest.mark.asyncio
async def test_create_note_duplicate_title(notes_app, api_client, repo_hub: RepositoryHub, user):
    # setup: create a note with the same title
    await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Dup Title",
        text="Text",
    )

    # action: attempt to create a duplicate title
    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes",
            json={"title": "Dup Title", "text": "Another"},
        )

    # check: validation error for duplicate title
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Note title must be unique"
