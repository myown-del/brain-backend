from datetime import datetime

from tests.integration.api.drafts.helpers import create_draft


async def test_get_draft_creation_stats(notes_app, api_client, repo_hub, user):
    await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Draft 1",
        created_at=datetime(2024, 1, 1, 10, 0, 0),
        updated_at=datetime(2024, 1, 1, 10, 0, 0),
    )
    await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Draft 2",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
    )
    await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Draft 3",
        created_at=datetime(2024, 1, 2, 9, 0, 0),
        updated_at=datetime(2024, 1, 2, 9, 0, 0),
    )

    async with api_client(notes_app) as client:
        response = await client.get("/api/drafts/creation-stats")

    assert response.status_code == 200
    assert response.json() == [
        {"date": "2024-01-01", "count": 2},
        {"date": "2024-01-02", "count": 1},
    ]


async def test_get_draft_creation_stats_with_timezone(notes_app, api_client, repo_hub, user):
    await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Boundary Draft 1",
        created_at=datetime(2024, 1, 2, 0, 30, 0),
        updated_at=datetime(2024, 1, 2, 0, 30, 0),
    )
    await create_draft(
        repo_hub=repo_hub,
        user=user,
        text="Boundary Draft 2",
        created_at=datetime(2024, 1, 2, 8, 30, 0),
        updated_at=datetime(2024, 1, 2, 8, 30, 0),
    )

    async with api_client(notes_app) as client:
        response = await client.get("/api/drafts/creation-stats?timezone=America/Los_Angeles")

    assert response.status_code == 200
    assert response.json() == [
        {"date": "2024-01-01", "count": 1},
        {"date": "2024-01-02", "count": 1},
    ]


async def test_get_draft_creation_stats_invalid_timezone_returns_bad_request(
    notes_app,
    api_client,
    user,
):
    async with api_client(notes_app) as client:
        response = await client.get("/api/drafts/creation-stats?timezone=Bad/Timezone")

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid timezone"}
