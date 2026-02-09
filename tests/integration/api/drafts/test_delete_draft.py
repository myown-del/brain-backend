from uuid import uuid4

import pytest
from fastapi import FastAPI
from starlette import status

from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.conftest import ApiClientFactory
from tests.integration.api.drafts.helpers import create_draft


@pytest.mark.asyncio
async def test_delete_draft_success(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
    user: User,
) -> None:
    # setup: create user draft
    draft = await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Delete me",
    )

    # action: delete draft
    async with api_client(notes_app) as client:
        response = await client.request(
            method="DELETE",
            url=f"/api/drafts/{draft.id}",
        )

    # check: draft is removed
    assert response.status_code == status.HTTP_204_NO_CONTENT
    stored = await repo_hub.drafts.get_by_id(draft_id=draft.id)
    assert stored is None


@pytest.mark.asyncio
async def test_delete_draft_not_found(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
) -> None:
    # setup: use random id
    draft_id = uuid4()

    # action: delete missing draft
    async with api_client(notes_app) as client:
        response = await client.request(
            method="DELETE",
            url=f"/api/drafts/{draft_id}",
        )

    # check: not found response
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Draft not found"


@pytest.mark.asyncio
async def test_delete_draft_forbidden(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
) -> None:
    # setup: create another user draft
    other_user = User(
        id=uuid4(),
        telegram_id=111222,
        username="other_user",
        first_name="Other",
        last_name="User",
    )
    await repo_hub.users.create(entity=other_user)
    draft = await create_draft(
        repo_hub=repo_hub,
        user=other_user,
        text="Other draft",
    )

    # action: try deleting foreign draft
    async with api_client(notes_app) as client:
        response = await client.request(
            method="DELETE",
            url=f"/api/drafts/{draft.id}",
        )

    # check: forbidden response
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Forbidden"
