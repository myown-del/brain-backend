import pytest
from starlette import status

from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.notes.helpers import create_keyword_note
from tests.integration.utils.uow import commit_repo_hub


@pytest.mark.asyncio
async def test_get_wikilink_suggestions(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    # setup: create keyword note and keyword without note
    await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Alpha",
        text="Text",
    )
    await repo_hub.keywords.ensure_keywords(user_id=user.id, names=["Beta"])
    await commit_repo_hub(repo_hub)

    # action: request wikilink suggestions
    async with api_client(notes_app) as client:
        response = await client.request(
            method="GET",
            url="/api/notes/wikilink-suggestions?query=a",
        )

    # check: response includes keyword note and missing note keyword
    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload == [
        {"title": "Alpha", "represents_keyword": True},
        {"title": "Beta", "represents_keyword": False},
    ]
