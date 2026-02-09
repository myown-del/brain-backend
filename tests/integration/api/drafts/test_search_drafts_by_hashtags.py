import pytest
from fastapi import FastAPI
from starlette import status

from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.conftest import ApiClientFactory
from tests.integration.api.drafts.helpers import create_draft


@pytest.mark.asyncio
async def test_search_drafts_filters_by_single_hashtag(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
    user: User,
) -> None:
    # setup: create drafts with different hashtags
    target = await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Task #work",
        hashtags=["work"],
    )
    await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Task #personal",
        hashtags=["personal"],
    )

    # action: filter by one hashtag
    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/drafts/search",
            json={"hashtags": ["work"]},
        )

    # check: only matching draft is returned
    assert response.status_code == status.HTTP_200_OK
    ids = [item["id"] for item in response.json()]
    assert ids == [str(target.id)]


@pytest.mark.asyncio
async def test_search_drafts_filters_by_multiple_hashtags(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
    user: User,
) -> None:
    # setup: create drafts with overlapping hashtags
    target = await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Roadmap #work #ai",
        hashtags=["work", "ai"],
    )
    await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Single hashtag #work",
        hashtags=["work"],
    )

    # action: filter by two hashtags
    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/drafts/search",
            json={"hashtags": ["work", "#ai"]},
        )

    # check: only draft containing both hashtags is returned
    assert response.status_code == status.HTTP_200_OK
    ids = [item["id"] for item in response.json()]
    assert ids == [str(target.id)]
