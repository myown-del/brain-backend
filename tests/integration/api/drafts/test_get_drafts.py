from datetime import datetime

import pytest
from fastapi import FastAPI
from starlette import status

from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.conftest import ApiClientFactory
from tests.integration.api.drafts.helpers import create_draft


@pytest.mark.asyncio
async def test_get_drafts_returns_all_user_drafts(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
    user: User,
) -> None:
    # setup: create two drafts for current user
    first = await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="First draft",
    )
    second = await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Second draft",
    )

    # action: request all drafts
    async with api_client(notes_app) as client:
        response = await client.request(
            method="GET",
            url="/api/drafts",
        )

    # check: both drafts are returned
    assert response.status_code == status.HTTP_200_OK
    ids = {item["id"] for item in response.json()}
    assert ids == {str(first.id), str(second.id)}


@pytest.mark.asyncio
async def test_search_drafts_post_filters_by_date_range(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
    user: User,
) -> None:
    # setup: create drafts with different dates
    in_range = await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="In range",
        created_at=datetime(2024, 1, 2, 3, 4, 5),
        updated_at=datetime(2024, 1, 2, 3, 4, 5),
    )
    await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Out range",
        created_at=datetime(2024, 2, 2, 3, 4, 5),
        updated_at=datetime(2024, 2, 2, 3, 4, 5),
    )

    # action: search drafts with date filters
    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/drafts/search",
            json={
                "from_date": "2024-01-01T00:00:00",
                "to_date": "2024-01-03T00:00:00",
            },
        )

    # check: only in-range draft is returned
    assert response.status_code == status.HTTP_200_OK
    ids = [item["id"] for item in response.json()]
    assert ids == [str(in_range.id)]
