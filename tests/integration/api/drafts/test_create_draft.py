import pytest
from fastapi import FastAPI
from starlette import status
from uuid import UUID

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
