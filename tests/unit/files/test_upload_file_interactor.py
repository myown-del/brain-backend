import re
from unittest.mock import Mock, AsyncMock

import pytest

from brain.application.interactors.upload_file import UploadFileInteractor
from brain.config.models import S3Config


@pytest.mark.asyncio
async def test_upload_file_uses_filename_extension():
    # setup: create interactor with mocked dependencies
    mock_file_storage = Mock()
    mock_s3_files_repo = AsyncMock()
    s3_config = S3Config(
        external_host="http://files.example.com",
        endpoint_url="http://localhost:9000",
        access_key_id="key",
        secret_access_key="secret",
        bucket_name="test-bucket",
    )
    interactor = UploadFileInteractor(
        file_storage=mock_file_storage,
        s3_files_repo=mock_s3_files_repo,
        s3_config=s3_config,
    )

    # action: upload file with extension in filename
    file = await interactor.upload_file(
        filename="report.PDF",
        content=b"content",
        content_type="application/pdf",
    )

    # check: storage and repository get called with generated object name
    assert mock_file_storage.upload.call_count == 1
    upload_call = mock_file_storage.upload.call_args.kwargs
    assert upload_call["content"] == b"content"
    assert upload_call["content_type"] == "application/pdf"
    assert re.fullmatch(r"[0-9a-f-]+\.pdf", upload_call["object_name"])
    assert file.name == upload_call["object_name"]
    assert file.path == upload_call["object_name"]
    assert file.content_type == "application/pdf"
    assert file.id is not None
    assert file.url == f"http://files.example.com/{upload_call['object_name']}"
    assert mock_s3_files_repo.create.await_count == 1
    create_call = mock_s3_files_repo.create.await_args.kwargs
    assert create_call["entity"].name == file.name
    assert create_call["entity"].path == file.path
    assert create_call["entity"].content_type == file.content_type


@pytest.mark.asyncio
async def test_upload_file_uses_bin_when_filename_has_no_extension():
    # setup: create interactor with mocked dependencies
    mock_file_storage = Mock()
    mock_s3_files_repo = AsyncMock()
    s3_config = S3Config(
        external_host="http://files.example.com",
        endpoint_url="http://localhost:9000",
        access_key_id="key",
        secret_access_key="secret",
        bucket_name="test-bucket",
    )
    interactor = UploadFileInteractor(
        file_storage=mock_file_storage,
        s3_files_repo=mock_s3_files_repo,
        s3_config=s3_config,
    )

    # action: upload file with no extension in filename
    file = await interactor.upload_file(
        filename="README",
        content=b"content",
    )

    # check: fallback extension is used
    upload_call = mock_file_storage.upload.call_args.kwargs
    assert re.fullmatch(r"[0-9a-f-]+\.bin", upload_call["object_name"])
    assert file.name == upload_call["object_name"]
    assert file.path == upload_call["object_name"]
    assert file.content_type == "application/octet-stream"
    assert file.url == f"http://files.example.com/{upload_call['object_name']}"
