from uuid import uuid4
from unittest.mock import AsyncMock

import pytest

from brain.application.interactors.get_file import GetFileInteractor, FileNotFoundException
from brain.config.models import S3Config
from brain.domain.entities.s3_file import S3File


@pytest.mark.asyncio
async def test_get_file_returns_existing_file():
    # setup: create interactor with repository that has file
    file = S3File(
        id=uuid4(),
        name="file.jpg",
        path="folder/file.jpg",
        content_type="image/jpeg",
    )
    mock_s3_files_repo = AsyncMock()
    mock_s3_files_repo.get_by_id.return_value = file
    interactor = GetFileInteractor(
        s3_files_repo=mock_s3_files_repo,
        s3_config=S3Config(
            external_host="http://files.example.com",
            endpoint_url="http://localhost:9000",
            access_key_id="key",
            secret_access_key="secret",
            bucket_name="test-bucket",
        ),
    )

    # action: get file by id
    result = await interactor.get_file_by_id(file_id=file.id)

    # check: same file is returned
    assert result.id == file.id
    assert result.name == file.name
    assert result.path == file.path
    assert result.content_type == file.content_type
    assert result.url == "http://files.example.com/folder/file.jpg"


@pytest.mark.asyncio
async def test_get_file_raises_when_file_not_found():
    # setup: create interactor with empty repository response
    mock_s3_files_repo = AsyncMock()
    mock_s3_files_repo.get_by_id.return_value = None
    interactor = GetFileInteractor(
        s3_files_repo=mock_s3_files_repo,
        s3_config=S3Config(
            external_host="http://files.example.com",
            endpoint_url="http://localhost:9000",
            access_key_id="key",
            secret_access_key="secret",
            bucket_name="test-bucket",
        ),
    )

    # action + check: not found raises domain exception
    with pytest.raises(FileNotFoundException):
        await interactor.get_file_by_id(file_id=uuid4())
