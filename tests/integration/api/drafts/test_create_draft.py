from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from starlette import status

from brain.domain.entities.s3_file import S3File
from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.conftest import ApiClientFactory


@pytest.mark.asyncio
async def test_create_draft_success(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
    user: User,
) -> None:
    # setup: prepare create payload
    payload = {"text": "Draft body with #work #ideas"}

    # action: create draft via API
    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/drafts",
            json=payload,
        )

    # check: draft and hashtags are persisted
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    stored = await repo_hub.drafts.get_by_id(draft_id=UUID(body["id"]))
    assert stored is not None
    assert stored.user_id == user.id
    assert stored.text == payload["text"]
    assert sorted(body["hashtags"]) == ["ideas", "work"]


@pytest.mark.asyncio
async def test_create_draft_with_file_id(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
    user: User,
) -> None:
    # setup: create a file and prepare create payload
    file = S3File(
        id=uuid4(),
        name="document.txt",
        path=f"uploads/{user.id}/document.txt",
        content_type="text/plain",
    )
    await repo_hub.s3_files.create(entity=file)
    payload = {"text": "Draft with file", "file_id": str(file.id)}

    # action: create draft via API
    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/drafts",
            json=payload,
        )

    # check: draft stores attached file id
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["file"] is not None
    assert body["file"]["id"] == str(file.id)
    assert body["file"]["path"] == file.path
    assert body["file"]["url"].endswith(file.path)
    stored = await repo_hub.drafts.get_by_id(draft_id=UUID(body["id"]))
    assert stored is not None
    assert stored.file_id == file.id
