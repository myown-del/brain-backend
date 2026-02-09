import pytest
from fastapi import FastAPI
from starlette import status

from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.conftest import ApiClientFactory
from tests.integration.api.drafts.helpers import create_draft


@pytest.mark.asyncio
async def test_search_drafts_by_text_returns_matches(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
    user: User,
) -> None:
    # setup: create drafts with different text values
    first = await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Alpha text",
    )
    await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Beta text",
    )

    # action: search by text query through drafts search endpoint
    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/drafts/search",
            json={"text_query": "alpha"},
        )

    # check: only matching draft is returned
    assert response.status_code == status.HTTP_200_OK
    ids = [item["id"] for item in response.json()]
    assert ids == [str(first.id)]


@pytest.mark.asyncio
async def test_post_search_combines_text_and_hashtag_filters(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
    user: User,
) -> None:
    # setup: create drafts with overlapping text and hashtags
    target = await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Brainstorm about AI #ai #notes",
        hashtags=["ai", "notes"],
    )
    await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Brainstorm unrelated #misc",
        hashtags=["misc"],
    )

    # action: apply text and hashtag filters together
    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/drafts/search",
            json={"text_query": "brainstorm", "hashtags": ["#ai"]},
        )

    # check: only the matching draft is returned
    assert response.status_code == status.HTTP_200_OK
    ids = [item["id"] for item in response.json()]
    assert ids == [str(target.id)]
