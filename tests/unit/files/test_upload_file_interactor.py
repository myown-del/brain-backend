import re
from unittest.mock import Mock

import pytest

from brain.application.interactors.upload_file import UploadFileInteractor


@pytest.mark.asyncio
async def test_upload_file_uses_filename_extension():
    mock_file_storage = Mock()
    mock_file_storage.upload.return_value = "http://storage/file.pdf"
    interactor = UploadFileInteractor(file_storage=mock_file_storage)

    url = await interactor.upload_file(
        filename="report.PDF",
        content=b"content",
        content_type="application/pdf",
    )

    assert url == "http://storage/file.pdf"
    assert mock_file_storage.upload.call_count == 1
    upload_call = mock_file_storage.upload.call_args.kwargs
    assert upload_call["content"] == b"content"
    assert upload_call["content_type"] == "application/pdf"
    assert re.fullmatch(r"[0-9a-f-]+\.pdf", upload_call["object_name"])


@pytest.mark.asyncio
async def test_upload_file_uses_bin_when_filename_has_no_extension():
    mock_file_storage = Mock()
    mock_file_storage.upload.return_value = "http://storage/file.bin"
    interactor = UploadFileInteractor(file_storage=mock_file_storage)

    await interactor.upload_file(
        filename="README",
        content=b"content",
    )

    upload_call = mock_file_storage.upload.call_args.kwargs
    assert re.fullmatch(r"[0-9a-f-]+\.bin", upload_call["object_name"])
