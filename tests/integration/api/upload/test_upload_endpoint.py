import re
from uuid import UUID
from unittest.mock import MagicMock
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from dishka import make_async_container, Provider, Scope, provide
from dishka.integrations.fastapi import setup_dishka

from brain.application.abstractions.repositories.s3_files import IS3FilesRepository
from brain.application.abstractions.storage.files import IFileStorage
from brain.application.interactors.upload_file import UploadFileInteractor
from brain.presentation.api.factory import create_bare_app
from brain.config.models import APIConfig, S3Config


@pytest.fixture
def client(event_loop):
    # setup: api and s3 config used by app and URL builder
    api_config = APIConfig(
        internal_host="0.0.0.0",
        external_host="localhost",
        port=8080,
    )
    s3_config = S3Config(
        external_host="http://files.example.com",
        endpoint_url="http://localhost:9000",
        access_key_id="key",
        secret_access_key="secret",
        bucket_name="test-bucket",
    )

    # setup: mocked storage and repository dependencies
    mock_file_storage = MagicMock(spec=IFileStorage)
    mock_s3_files_repo = AsyncMock(spec=IS3FilesRepository)

    # Provider
    class MockProvider(Provider):
        scope = Scope.APP

        @provide
        def get_upload_file_interactor(
            self,
            file_storage: IFileStorage,
            s3_files_repo: IS3FilesRepository,
        ) -> UploadFileInteractor:
            return UploadFileInteractor(
                file_storage=file_storage,
                s3_files_repo=s3_files_repo,
            )

        @provide(provides=IFileStorage)
        def get_file_storage(self) -> IFileStorage:
            return mock_file_storage

        @provide(provides=IS3FilesRepository)
        def get_s3_files_repo(self) -> IS3FilesRepository:
            return mock_s3_files_repo

        @provide
        def get_s3_config(self) -> S3Config:
            return s3_config

    # App
    app = create_bare_app(api_config)

    # Container
    container = make_async_container(MockProvider())
    setup_dishka(container=container, app=app)

    with TestClient(app) as client:
        yield client

    event_loop.run_until_complete(container.close())


def test_upload_image(client):
    # action: upload image file
    files = {"file": ("test.jpg", b"content", "image/jpeg")}
    response = client.request(method="POST", url="/api/file/upload", files=files)

    # check: file is uploaded and public URL is built dynamically
    assert response.status_code == 200
    payload = response.json()
    assert re.match(r"^http://files.example.com/[0-9a-f-]+\.jpg$", payload["url"])
    assert re.match(r"^[0-9a-f-]+\.jpg$", payload["name"])
    assert payload["path"] == payload["name"]
    assert UUID(payload["id"])
    assert payload["content_type"] == "image/jpeg"
    assert payload["created_at"] is None


def test_upload_file_supports_non_image_content(client):
    # action: upload non-image file
    files = {"file": ("report.pdf", b"content", "application/pdf")}
    response = client.request(method="POST", url="/api/file/upload", files=files)

    # check: extension and URL path are correct
    assert response.status_code == 200
    payload = response.json()
    assert re.match(r"^http://files.example.com/[0-9a-f-]+\.pdf$", payload["url"])
    assert re.match(r"^[0-9a-f-]+\.pdf$", payload["name"])
    assert payload["path"] == payload["name"]
    assert UUID(payload["id"])
    assert payload["content_type"] == "application/pdf"
    assert payload["created_at"] is None


def test_upload_file_without_extension(client):
    # action: upload file without extension in name
    files = {"file": ("README", b"content", "text/plain")}
    response = client.request(method="POST", url="/api/file/upload", files=files)

    # check: default bin extension and URL path are correct
    assert response.status_code == 200
    payload = response.json()
    assert re.match(r"^http://files.example.com/[0-9a-f-]+\.bin$", payload["url"])
    assert re.match(r"^[0-9a-f-]+\.bin$", payload["name"])
    assert payload["path"] == payload["name"]
    assert UUID(payload["id"])
    assert payload["content_type"] == "text/plain"
    assert payload["created_at"] is None
