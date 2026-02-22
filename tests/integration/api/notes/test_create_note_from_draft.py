from uuid import uuid4

import pytest
from starlette import status

from brain.config.models import Config
from brain.domain.entities.s3_file import S3File
from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.drafts.helpers import create_draft
from tests.integration.api.notes.helpers import create_keyword_note
from tests.integration.utils.uow import commit_repo_hub


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
async def test_create_note_from_draft_appends_attached_file_markdown(
    notes_app,
    api_client,
    dishka_request,
    repo_hub: RepositoryHub,
    user,
):
    # setup: create file-backed draft
    config = await dishka_request.get(Config)
    file = S3File(
        id=uuid4(),
        name="draft-image.png",
        path="uploads/draft-image.png",
        content_type="image/png",
    )
    await repo_hub.s3_files.create(entity=file)
    await commit_repo_hub(repo_hub)
    draft = await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Draft text",
        file_id=file.id,
    )

    # action: create note from draft with attachment
    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes/create-from-draft",
            json={"draft_id": str(draft.id), "title": "From Draft With File"},
        )

    # check: attachment markdown is appended to note text
    assert response.status_code == status.HTTP_201_CREATED
    payload = response.json()
    expected_text = f"Draft text\n\n![{file.name}]({config.s3.external_host}/{file.path})"
    assert payload["text"] == expected_text
    stored_note = await repo_hub.notes.get_by_title(
        user_id=user.id,
        title="From Draft With File",
        exact_match=True,
    )
    assert stored_note is not None
    assert stored_note.text == expected_text


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
    await commit_repo_hub(repo_hub)
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


@pytest.mark.asyncio
async def test_create_note_from_draft_rolls_back_when_note_creation_fails(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Duplicate Title",
        text="existing",
    )
    draft = await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Draft that must survive rollback",
    )

    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes/create-from-draft",
            json={"draft_id": str(draft.id), "title": "Duplicate Title"},
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Note title must be unique"
    stored_draft = await repo_hub.drafts.get_by_id(draft_id=draft.id)
    assert stored_draft is not None
