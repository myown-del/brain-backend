import pytest
import json
import zipfile
import io
from unittest.mock import AsyncMock, Mock
from brain.application.interactors.notes.import_notes import ImportNotesInteractor
from brain.application.interactors.notes.exceptions import NoteTitleAlreadyExistsException
from uuid import uuid4


@pytest.mark.asyncio
async def test_import_notes():
    # Setup
    user_id = 123
    mock_user_interactor = AsyncMock()
    mock_notes_repo = AsyncMock()
    mock_graph_repo = AsyncMock()
    mock_keyword_service = AsyncMock()
    mock_title_service = AsyncMock()
    mock_sync_service = AsyncMock()

    interactor = ImportNotesInteractor(
        mock_user_interactor,
        mock_notes_repo,
        mock_graph_repo,
        mock_keyword_service,
        mock_title_service,
        mock_sync_service,
    )

    mock_user = Mock(id=uuid4(), telegram_id=user_id)
    mock_user_interactor.get_user_by_telegram_id.return_value = mock_user

    # Create valid zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        note_data = {
            "title": "Imported Note",
            "text": "Imported Content",
        }
        zf.writestr("Imported Note.json", json.dumps(note_data))

    zip_bytes = zip_buffer.getvalue()

    # Mock behavior
    mock_keyword_service.ensure_keyword_for_title.return_value = uuid4()

    # Execute
    await interactor.import_notes(user_id, zip_bytes)

    # Verify
    mock_title_service.ensure_unique_title.assert_called_with(mock_user.id, "Imported Note")
    mock_notes_repo.create.assert_called_once()
    saved_note = mock_notes_repo.create.call_args[0][0]
    assert saved_note.title == "Imported Note"
    assert saved_note.text == "Imported Content"
    mock_graph_repo.upsert_note.assert_called_once_with(saved_note)
    mock_sync_service.sync.assert_called_once_with(saved_note)


@pytest.mark.asyncio
async def test_import_skip_existing():
    # Setup
    user_id = 123
    mock_user_interactor = AsyncMock()
    mock_notes_repo = AsyncMock()
    mock_graph_repo = AsyncMock()
    mock_keyword_service = AsyncMock()
    mock_title_service = AsyncMock()
    mock_sync_service = AsyncMock()

    interactor = ImportNotesInteractor(
        mock_user_interactor,
        mock_notes_repo,
        mock_graph_repo,
        mock_keyword_service,
        mock_title_service,
        mock_sync_service,
    )

    mock_user = Mock(id=uuid4(), telegram_id=user_id)
    mock_user_interactor.get_user_by_telegram_id.return_value = mock_user

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("Existing.json", json.dumps({"title": "Existing", "text": "Content"}))

    mock_title_service.ensure_unique_title.side_effect = NoteTitleAlreadyExistsException()

    # Execute
    await interactor.import_notes(user_id, zip_buffer.getvalue())

    # Verify
    mock_notes_repo.create.assert_not_called()
