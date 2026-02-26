import pytest
import zipfile
import io
import json
from unittest.mock import AsyncMock, Mock
from brain.application.interactors.notes.export_notes import ExportNotesInteractor
from brain.domain.entities.note import Note
from uuid import uuid4


@pytest.mark.asyncio
async def test_export_notes():
    # Setup
    user_id = 123
    mock_user_interactor = AsyncMock()
    mock_notes_repo = AsyncMock()

    interactor = ExportNotesInteractor(mock_user_interactor, mock_notes_repo)

    # Mock data
    mock_user = Mock(id=uuid4(), telegram_id=user_id)
    mock_user_interactor.get_user_by_telegram_id.return_value = mock_user

    note_id = uuid4()
    note_title = "Test Note"
    note = Note(
        id=note_id,
        user_id=mock_user.id,
        title=note_title,
        text="Content",
        is_archived=True,
        represents_keyword_id=None,
    )
    mock_notes_repo.get_by_user_telegram_id.return_value = [note]

    # Execute
    zip_bytes = await interactor.export_notes(user_id)

    # Verify
    assert zip_bytes is not None

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        files = zf.namelist()
        assert "Test Note.json" in files

        with zf.open("Test Note.json") as f:
            data = json.load(f)
            assert data["title"] == note_title
            assert data["text"] == "Content"
            assert data["id"] == str(note_id)
            assert data["is_archived"] is True
