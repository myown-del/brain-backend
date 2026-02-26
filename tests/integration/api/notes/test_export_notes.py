import io
import json
import zipfile

import pytest
from starlette import status

from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.notes.helpers import create_keyword_note


@pytest.mark.asyncio
async def test_export_notes(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    # setup: create a note for export
    note = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title="Alpha Note",
        text="Body",
        is_archived=True,
    )

    # action: request export
    async with api_client(notes_app) as client:
        response = await client.request(
            method="GET",
            url="/api/notes/export",
        )

    # check: response headers and zip content
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/zip"
    assert response.headers["content-disposition"] == "attachment; filename=notes_export.zip"

    with zipfile.ZipFile(
        file=io.BytesIO(response.content),
    ) as zip_file:
        assert "Alpha Note.json" in zip_file.namelist()
        with zip_file.open(name="Alpha Note.json") as entry:
            data = json.loads(entry.read().decode("utf-8"))
    assert data["id"] == str(note.id)
    assert data["title"] == "Alpha Note"
    assert data["text"] == "Body"
    assert data["is_archived"] is True
