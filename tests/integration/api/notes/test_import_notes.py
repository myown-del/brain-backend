import io
import json
import zipfile

import pytest
from starlette import status

from brain.infrastructure.db.repositories.hub import RepositoryHub


def make_zip_with_note(title: str, text: str | None, is_archived: bool = False) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(
        file=buffer,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as zip_file:
        payload = {"title": title, "text": text, "is_archived": is_archived}
        zip_file.writestr(
            zinfo_or_arcname=f"{title}.json",
            data=json.dumps(payload),
        )
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_import_notes_success(
    notes_app,
    api_client,
    repo_hub: RepositoryHub,
    user,
):
    # setup: build a valid zip with one note
    zip_bytes = make_zip_with_note(
        title="Imported Note",
        text="Imported Body",
        is_archived=True,
    )

    # action: upload zip file
    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes/import",
            files={"file": ("notes.zip", zip_bytes, "application/zip")},
        )

    # check: note created in database
    assert response.status_code == status.HTTP_204_NO_CONTENT
    stored = await repo_hub.notes.get_by_title(
        user_id=user.id,
        title="Imported Note",
        exact_match=True,
    )
    assert stored is not None
    assert stored.text == "Imported Body"
    assert stored.is_archived is True


@pytest.mark.asyncio
async def test_import_notes_invalid_extension(notes_app, api_client):
    # setup: prepare a non-zip file upload
    bad_file = ("notes.txt", b"content", "text/plain")

    # action: upload non-zip file
    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes/import",
            files={"file": bad_file},
        )

    # check: validation error
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "File must be a .zip extension"


@pytest.mark.asyncio
async def test_import_notes_invalid_zip(notes_app, api_client):
    # setup: prepare invalid zip content
    invalid_zip = ("notes.zip", b"bad-zip", "application/zip")

    # action: upload invalid zip
    async with api_client(notes_app) as client:
        response = await client.request(
            method="POST",
            url="/api/notes/import",
            files={"file": invalid_zip},
        )

    # check: error response for invalid zip
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid zip file"
