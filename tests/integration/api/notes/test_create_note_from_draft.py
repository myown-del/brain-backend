from uuid import uuid4

import pytest
from starlette import status

from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.drafts.helpers import create_draft
from tests.integration.api.notes.helpers import create_keyword_note


@pytest.mark.asyncio
async def test_create_note_from_draft_success(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    # setup: create user draft
    draft = await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Draft text",
    )

    # action: create note from draft with explicit title
    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes/create-from-draft",
            json={"draft_id": str(draft.id), "title": "From Draft"},
        )

    # check: note is created and draft is deleted
    assert response.status_code == status.HTTP_201_CREATED
    payload = response.json()
    assert payload["title"] == "From Draft"
    assert payload["text"] == "Draft text"
    stored_note = await repo_hub.notes.get_by_title(
        user_id=user.id,
        title="From Draft",
        exact_match=True,
    )
    assert stored_note is not None
    assert stored_note.text == "Draft text"
    stored_draft = await repo_hub.drafts.get_by_id(draft_id=draft.id)
    assert stored_draft is None


@pytest.mark.asyncio
async def test_create_note_from_draft_generates_title(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    # setup: reserve first untitled and create user draft
    await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Untitled 1",
        text="Existing",
    )
    draft = await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Draft body",
    )

    # action: create note from draft without title
    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes/create-from-draft",
            json={"draft_id": str(draft.id), "title": None},
        )

    # check: generated title is used and draft is deleted
    assert response.status_code == status.HTTP_201_CREATED
    payload = response.json()
    assert payload["title"] == "Untitled 2"
    assert payload["text"] == "Draft body"
    stored_draft = await repo_hub.drafts.get_by_id(draft_id=draft.id)
    assert stored_draft is None


@pytest.mark.asyncio
async def test_create_note_from_draft_not_found(
    notes_app,
    api_client,
):
    # setup: use random id
    draft_id = uuid4()

    # action: create note from missing draft
    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes/create-from-draft",
            json={"draft_id": str(draft_id), "title": "From Draft"},
        )

    # check: draft not found response
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Draft not found"


@pytest.mark.asyncio
async def test_create_note_from_draft_forbidden(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
):
    # setup: create draft that belongs to another user
    other_user = User(
        id=uuid4(),
        telegram_id=123456,
        username="other_user",
        first_name="Other",
        last_name="User",
    )
    await repo_hub.users.create(entity=other_user)
    draft = await create_draft(
        repo_hub=repo_hub,
        user=other_user,
        text="Private draft",
    )

    # action: try to create note from foreign draft
    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes/create-from-draft",
            json={"draft_id": str(draft.id), "title": "From Draft"},
        )

    # check: forbidden response and draft is kept
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Forbidden"
    stored_draft = await repo_hub.drafts.get_by_id(draft_id=draft.id)
    assert stored_draft is not None
