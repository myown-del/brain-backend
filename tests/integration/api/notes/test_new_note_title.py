import pytest
from starlette import status

from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.notes.helpers import create_keyword_note


@pytest.mark.asyncio
async def test_get_new_note_title_default(notes_app, api_client, user):
    # setup: no existing notes for user

    # action: request next title
    async with api_client(notes_app) as client:
        response = await client.request(
            method="GET",
            url="/api/notes/new-title",
        )

    # check: default untitled title
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"title": "Untitled 1"}


@pytest.mark.asyncio
async def test_get_new_note_title_skips_existing(notes_app, api_client, repo_hub: RepositoryHub, user):
    # setup: create an existing untitled note
    await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Untitled 1",
    )

    # action: request next title
    async with api_client(notes_app) as client:
        response = await client.request(
            method="GET",
            url="/api/notes/new-title",
        )

    # check: next untitled title is returned
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"title": "Untitled 2"}
