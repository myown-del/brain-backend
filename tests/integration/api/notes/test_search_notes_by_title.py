from datetime import datetime

import pytest
from starlette import status

from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.notes.helpers import create_keyword_note


@pytest.mark.asyncio
async def test_search_notes_by_title_default_exact_match(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    # setup: create notes with similar titles
    await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Test Note",
        text="Content",
    )
    await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Test Note Extended",
        text="Content",
    )

    # action: request search without exact_match
    async with api_client(notes_app) as client:
        response = await client.request(
            method="GET",
            url="/api/notes/search/by-title?query=Test Note",
        )

    # check: response returns both matching notes
    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    titles = {item["title"] for item in payload}
    assert titles == {"Test Note", "Test Note Extended"}


@pytest.mark.asyncio
async def test_search_notes_by_title_exact_match_true(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    # setup: create notes with similar titles
    await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Test Note",
        text="Content",
    )
    await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Test Note Extended",
        text="Content",
    )

    # action: request search with exact_match=true
    async with api_client(notes_app) as client:
        response = await client.request(
            method="GET",
            url="/api/notes/search/by-title?query=Test Note&exact_match=true",
        )

    # check: response returns only exact title match
    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert [item["title"] for item in payload] == ["Test Note"]


@pytest.mark.asyncio
async def test_search_notes_by_title_pinned_first_default_true(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Search Note",
        text="Content",
        is_pinned=False,
    )
    pinned_note = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Search Note Pinned",
        text="Content",
        is_pinned=True,
    )

    async with api_client(notes_app) as client:
        response = await client.request(
            method="GET",
            url="/api/notes/search/by-title?query=Search Note",
        )

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload[0]["id"] == str(pinned_note.id)


@pytest.mark.asyncio
async def test_search_notes_by_title_pinned_first_false_uses_updated_at_order(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Search Old Pinned",
        text="Content",
        updated_at=datetime(2024, 1, 1, 0, 0, 0),
        is_pinned=True,
    )
    newest_regular = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Search New Regular",
        text="Content",
        updated_at=datetime(2024, 1, 2, 0, 0, 0),
        is_pinned=False,
    )

    async with api_client(notes_app) as client:
        response = await client.request(
            method="GET",
            url="/api/notes/search/by-title?query=Search&pinned_first=false",
        )

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload[0]["id"] == str(newest_regular.id)


@pytest.mark.asyncio
async def test_search_notes_by_title_excludes_archived_by_default(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Search Archived",
        text="Content",
        is_archived=True,
    )
    await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Search Active",
        text="Content",
        is_archived=False,
    )

    async with api_client(notes_app) as client:
        response = await client.request(
            method="GET",
            url="/api/notes/search/by-title?query=Search",
        )

    assert response.status_code == status.HTTP_200_OK
    assert {item["title"] for item in response.json()} == {"Search Active"}


@pytest.mark.asyncio
async def test_search_notes_by_title_include_archived_returns_all(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Search Archived Included",
        text="Content",
        is_archived=True,
    )
    await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Search Active Included",
        text="Content",
        is_archived=False,
    )

    async with api_client(notes_app) as client:
        response = await client.request(
            method="GET",
            url="/api/notes/search/by-title?query=Search&include_archived=true",
        )

    assert response.status_code == status.HTTP_200_OK
    assert {item["title"] for item in response.json()} == {
        "Search Archived Included",
        "Search Active Included",
    }
