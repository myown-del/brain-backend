from uuid import uuid4

import pytest
from starlette import status

from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.drafts.helpers import create_draft
from tests.integration.api.notes.helpers import create_keyword_note


@pytest.mark.asyncio
async def test_append_from_draft_success(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    note = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Note",
        text="Current text",
    )
    draft = await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Draft text",
    )

    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes/append-from-draft",
            json={"note_id": str(note.id), "draft_id": str(draft.id)},
        )

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["id"] == str(note.id)
    assert payload["text"] == "Current text\nDraft text"

    stored_note = await repo_hub.notes.get_by_id(note.id)
    assert stored_note is not None
    assert stored_note.text == "Current text\nDraft text"
    assert await repo_hub.drafts.get_by_id(draft_id=draft.id) is None


@pytest.mark.asyncio
async def test_append_from_draft_note_not_found(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    draft = await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Draft text",
    )

    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes/append-from-draft",
            json={"note_id": str(uuid4()), "draft_id": str(draft.id)},
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Note not found"


@pytest.mark.asyncio
async def test_append_from_draft_draft_not_found(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    note = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Note",
        text="Current text",
    )

    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes/append-from-draft",
            json={"note_id": str(note.id), "draft_id": str(uuid4())},
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Draft not found"


@pytest.mark.asyncio
async def test_append_from_draft_forbidden(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    other_user = User(
        id=uuid4(),
        telegram_id=123321,
        username="other_user",
        first_name="Other",
        last_name="User",
    )
    await repo_hub.users.create(entity=other_user)
    note = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Note",
        text="Current text",
    )
    foreign_draft = await create_draft(
        repo_hub=repo_hub,
        user=other_user,
        text="Private draft",
    )

    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes/append-from-draft",
            json={"note_id": str(note.id), "draft_id": str(foreign_draft.id)},
        )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Forbidden"
