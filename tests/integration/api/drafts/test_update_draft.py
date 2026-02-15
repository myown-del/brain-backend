from uuid import uuid4

import pytest
from fastapi import FastAPI
from starlette import status

from brain.domain.entities.user import User
from brain.domain.entities.s3_file import S3File
from brain.domain.services.diffs import get_patches_str
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.conftest import ApiClientFactory
from tests.integration.api.drafts.helpers import create_draft


@pytest.mark.asyncio
async def test_update_draft_text_replacement(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
    user: User,
) -> None:
    # setup: create initial draft
    draft = await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Old draft #one",
    )

    # action: replace draft text
    async with api_client(notes_app) as client:
        response = await client.request(
            method="PATCH",
            url=f"/api/drafts/{draft.id}",
            json={"text": "New draft #two #three"},
        )

    # check: text and hashtags are updated
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["text"] == "New draft #two #three"
    assert sorted(body["hashtags"]) == ["three", "two"]
    stored = await repo_hub.drafts.get_by_id(draft_id=draft.id)
    assert stored is not None
    assert stored.text == "New draft #two #three"


@pytest.mark.asyncio
async def test_update_draft_with_patch(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
    user: User,
) -> None:
    # setup: create initial draft and patch payload
    draft = await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Hello #world",
    )
    patch = get_patches_str("Hello #world", "Hello patched #world #ai")

    # action: update draft using patch
    async with api_client(notes_app) as client:
        response = await client.request(
            method="PATCH",
            url=f"/api/drafts/{draft.id}",
            json={"patch": patch},
        )

    # check: patch is applied and hashtags synced
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["text"] == "Hello patched #world #ai"
    assert sorted(body["hashtags"]) == ["ai", "world"]


@pytest.mark.asyncio
async def test_update_draft_not_found(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
) -> None:
    # setup: use random id
    draft_id = uuid4()

    # action: update missing draft
    async with api_client(notes_app) as client:
        response = await client.request(
            method="PATCH",
            url=f"/api/drafts/{draft_id}",
            json={"text": "Updated"},
        )

    # check: not found response is returned
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Draft not found"


@pytest.mark.asyncio
async def test_update_draft_forbidden(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
) -> None:
    # setup: create another user and their draft
    other_user = User(
        id=uuid4(),
        telegram_id=321987,
        username="other_user",
        first_name="Other",
        last_name="User",
    )
    await repo_hub.users.create(entity=other_user)
    other_draft = await create_draft(
        repo_hub=repo_hub,
        user=other_user,
        text="Other text",
    )

    # action: update foreign draft
    async with api_client(notes_app) as client:
        response = await client.request(
            method="PATCH",
            url=f"/api/drafts/{other_draft.id}",
            json={"text": "Nope"},
        )

    # check: forbidden response is returned
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Forbidden"


@pytest.mark.asyncio
async def test_update_draft_invalid_patch_returns_bad_request(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
    user: User,
) -> None:
    # setup: create draft with existing text
    draft = await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Seed text",
    )

    # action: send malformed patch string
    async with api_client(notes_app) as client:
        response = await client.request(
            method="PATCH",
            url=f"/api/drafts/{draft.id}",
            json={"patch": "@@invalid@@"},
        )

    # check: API returns patch validation error
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Failed to apply patch"


@pytest.mark.asyncio
async def test_update_draft_file_id(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
    user: User,
) -> None:
    # setup: create draft and target file
    draft = await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Draft with attachment",
    )
    file = S3File(
        id=uuid4(),
        name="attach.txt",
        path=f"uploads/{user.id}/attach.txt",
        content_type="text/plain",
    )
    await repo_hub.s3_files.create(entity=file)

    # action: set draft file id
    async with api_client(notes_app) as client:
        response = await client.request(
            method="PATCH",
            url=f"/api/drafts/{draft.id}",
            json={"file_id": str(file.id)},
        )

    # check: file id is updated in response and storage
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["file"] is not None
    assert body["file"]["id"] == str(file.id)
    assert body["file"]["path"] == file.path
    assert body["file"]["url"].endswith(file.path)
    stored = await repo_hub.drafts.get_by_id(draft_id=draft.id)
    assert stored is not None
    assert stored.file_id == file.id
