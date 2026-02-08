from uuid import uuid4

import pytest
from starlette import status

from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.notes.helpers import create_keyword_note


@pytest.mark.asyncio
async def test_update_note_success(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    # setup: create a note owned by the user
    existing_note = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Old",
        text="Text",
    )

    # action: update note via API
    async with api_client(notes_app) as client:
        response = await client.request(
            method="PATCH",
            url=f"/api/notes/{existing_note.id}",
            json={"title": "New"},
        )

    # check: response and updated note match
    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["title"] == "New"
    stored = await repo_hub.notes.get_by_id(existing_note.id)
    assert stored is not None
    assert stored.title == "New"


@pytest.mark.asyncio
async def test_update_note_not_found(notes_app, api_client):
    # setup: use a random note id
    note_id = uuid4()

    # action: update a missing note
    async with api_client(notes_app) as client:
        response = await client.request(
            method="PATCH",
            url=f"/api/notes/{note_id}",
            json={"title": "New"},
        )

    # check: not found response
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Note not found"


@pytest.mark.asyncio
async def test_update_note_forbidden(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    # setup: create a note for another user
    other_user = User(
        id=uuid4(),
        telegram_id=321,
        username="other",
        first_name="Other",
        last_name="User",
    )
    await repo_hub.users.create(entity=other_user)
    note = await create_keyword_note(
        repo_hub=repo_hub,
        user=other_user,
        title="Other Note",
        text="Text",
    )

    # action: update note not owned by user
    async with api_client(notes_app) as client:
        response = await client.request(
            method="PATCH",
            url=f"/api/notes/{note.id}",
            json={"title": "New"},
        )

    # check: forbidden response
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Forbidden"


@pytest.mark.asyncio
async def test_update_note_requires_title(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    # setup: create a note to update
    note = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Title",
        text="Text",
    )

    # action: update note with null title
    async with api_client(notes_app) as client:
        response = await client.request(
            method="PATCH",
            url=f"/api/notes/{note.id}",
            json={"title": None},
        )

    # check: title required error
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Note title cannot be null"


@pytest.mark.asyncio
async def test_update_note_duplicate_title(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    # setup: create two notes
    note = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="First",
        text="Text",
    )
    await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Dup",
        text="Text",
    )

    # action: update note with existing title
    async with api_client(notes_app) as client:
        response = await client.request(
            method="PATCH",
            url=f"/api/notes/{note.id}",
            json={"title": "Dup"},
        )

    # check: duplicate title error
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Note title must be unique"


@pytest.mark.asyncio
async def test_update_note_can_set_is_pinned(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    note = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Pin Me",
        text="Text",
    )

    async with api_client(notes_app) as client:
        response = await client.request(
            method="PATCH",
            url=f"/api/notes/{note.id}",
            json={"is_pinned": True},
        )

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["is_pinned"] is True
    stored = await repo_hub.notes.get_by_id(note.id)
    assert stored is not None
    assert stored.is_pinned is True
