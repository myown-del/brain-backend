from uuid import uuid4

import pytest
from starlette import status

from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.notes.helpers import create_keyword_note
from tests.integration.utils.uow import commit_repo_hub


@pytest.mark.asyncio
async def test_delete_note_success(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    # setup: create a note owned by the user
    note = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Delete Me",
        text="Text",
    )

    # action: delete existing note
    async with api_client(notes_app) as client:
        response = await client.request(
            method="DELETE",
            url=f"/api/notes/{note.id}",
        )

    # check: note is removed from database
    assert response.status_code == status.HTTP_204_NO_CONTENT
    stored = await repo_hub.notes.get_by_id(note.id)
    assert stored is None


@pytest.mark.asyncio
async def test_delete_note_not_found(notes_app, api_client):
    # setup: use a random note id
    note_id = uuid4()

    # action: delete a missing note
    async with api_client(notes_app) as client:
        response = await client.request(
            method="DELETE",
            url=f"/api/notes/{note_id}",
        )

    # check: not found response
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Note not found"


@pytest.mark.asyncio
async def test_delete_note_forbidden(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    # setup: create a note for another user
    other_user = User(
        id=uuid4(),
        telegram_id=987,
        username="other",
        first_name="Other",
        last_name="User",
    )
    await repo_hub.users.create(entity=other_user)
    await commit_repo_hub(repo_hub)
    note = await create_keyword_note(
        repo_hub=repo_hub,
        user=other_user,
        title="Other Note",
        text="Text",
    )

    # action: delete note not owned by user
    async with api_client(notes_app) as client:
        response = await client.request(
            method="DELETE",
            url=f"/api/notes/{note.id}",
        )

    # check: forbidden response
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Forbidden"
